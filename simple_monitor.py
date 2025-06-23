        }
        
        function setTimeRange(minerName, minutes) {
            currentTimeRange = minutes;
            
            // Update button states
            const minerIdSafe = minerName.replace(/[^a-zA-Z0-9]/g, '');
            const container = document.querySelector(`[data-miner="${minerIdSafe}"]`);
            if (container) {
                container.querySelectorAll('.time-btn').forEach(btn => btn.classList.remove('active'));
                container.querySelector(`.time-btn[data-range="${minutes}"]`).classList.add('active');
            }
            
            // Filter chart data
            if (chartData[minerName]) {
                const chart = charts[minerName];
                if (chart) {
                    const now = new Date();
                    const cutoff = new Date(now.getTime() - (minutes * 60 * 1000));
                    
                    // Simple filtering - just show recent data
                    const recentCount = Math.min(Math.floor(minutes / 0.5), chartData[minerName].timestamps.length);
                    const labels = chartData[minerName].timestamps.slice(-recentCount);
                    const data = chartData[minerName].hashrates.slice(-recentCount);
                    
                    chart.data.labels = labels;
                    chart.data.datasets[0].data = data;
                    chart.update('none');
                }
            }
        }
        
        function initializeUI(data) {
            const minersGrid = document.getElementById('minersGrid');
            minersGrid.innerHTML = '';
            
            data.miners.forEach(miner => {
                if (miner.status === 'ONLINE') {
                    const minerIdSafe = miner.miner_name.replace(/[^a-zA-Z0-9]/g, '');
                    const minerCard = document.createElement('div');
                    minerCard.className = 'miner-card';
                    minerCard.innerHTML = `
                        <div class="miner-header">
                            <div class="miner-name">${miner.miner_name}</div>
                            <div class="status status-online" id="status-${minerIdSafe}">ONLINE</div>
                        </div>
                        <div id="metrics-${minerIdSafe}"></div>
                        <div class="chart-section" data-miner="${minerIdSafe}">
                            <div class="chart-controls">
                                <button class="time-btn" data-range="15" onclick="setTimeRange('${miner.miner_name}', 15)">15m</button>
                                <button class="time-btn active" data-range="30" onclick="setTimeRange('${miner.miner_name}', 30)">30m</button>
                                <button class="time-btn" data-range="60" onclick="setTimeRange('${miner.miner_name}', 60)">1h</button>
                                <button class="time-btn" data-range="180" onclick="setTimeRange('${miner.miner_name}', 180)">3h</button>
                            </div>
                            <div class="chart-container">
                                <canvas id="chart-${minerIdSafe}"></canvas>
                            </div>
                        </div>
                    `;
                    minersGrid.appendChild(minerCard);
                    
                    // Create chart
                    setTimeout(() => {
                        createChart(`chart-${minerIdSafe}`, miner.miner_name);
                    }, 100);
                } else {
                    const minerCard = document.createElement('div');
                    minerCard.className = 'miner-card';
                    minerCard.innerHTML = `
                        <div class="miner-header">
                            <div class="miner-name">${miner.miner_name}</div>
                            <div class="status status-offline">OFFLINE</div>
                        </div>
                        <div class="metric">
                            <span class="metric-label">IP Address</span>
                            <span class="metric-value">${miner.miner_ip}</span>
                        </div>
                    `;
                    minersGrid.appendChild(minerCard);
                }
            });
            
            isInitialized = true;
        }
        
        function updateMinerData(miner) {
            const minerIdSafe = miner.miner_name.replace(/[^a-zA-Z0-9]/g, '');
            const metricsElement = document.getElementById(`metrics-${minerIdSafe}`);
            
            if (miner.status === 'ONLINE' && metricsElement) {
                const deviation = (miner.hashrate_gh - miner.expected_hashrate_gh).toFixed(1);
                const deviationSign = deviation >= 0 ? '+' : '';
                
                metricsElement.innerHTML = `
                    <div class="metric">
                        <span class="metric-label">Hashrate</span>
                        <span class="metric-value">${miner.hashrate_th.toFixed(3)} TH/s</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Expected</span>
                        <span class="metric-value">${miner.expected_hashrate_th.toFixed(3)} TH/s</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Efficiency</span>
                        <span class="metric-value ${getEfficiencyClass(miner.hashrate_efficiency_pct)}">${miner.hashrate_efficiency_pct.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Deviation</span>
                        <span class="metric-value">${deviationSign}${deviation} GH/s</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Power</span>
                        <span class="metric-value">${miner.power_w.toFixed(1)} W</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Temperature</span>
                        <span class="metric-value">${miner.temperature_c.toFixed(1)}°C</span>
                    </div>
                `;
                
                updateChart(miner.miner_name, miner.hashrate_gh);
            }
        }
        
        function updateData() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('updateTime').textContent = 'Last updated: ' + new Date(data.timestamp).toLocaleString();
                    
                    // Update stats grid
                    document.getElementById('statsGrid').innerHTML = `
                        <div class="stat-card">
                            <div class="stat-label">Total Hashrate</div>
                            <div class="stat-value">${data.total_hashrate_th.toFixed(3)} TH/s</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Power</div>
                            <div class="stat-value">${data.total_power_w.toFixed(0)} W</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Fleet Efficiency</div>
                            <div class="stat-value ${getEfficiencyClass(data.fleet_efficiency)}">${data.fleet_efficiency.toFixed(1)}%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Miners Online</div>
                            <div class="stat-value">${data.online_count}/${data.total_count}</div>
                        </div>
                    `;
                    
                    // Initialize or update miners
                    if (!isInitialized) {
                        initializeUI(data);
                    } else {
                        data.miners.forEach(miner => {
                            updateMinerData(miner);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    document.getElementById('updateTime').textContent = 'Error: ' + error.message;
                });
        }
        
        // Start monitoring
        updateData();
        setInterval(updateData, 30000);
    </script>
</body></html>'''

def main():
    """Main function to run the simple BitAxe monitor"""
    
    # =================== EDIT YOUR CONFIGURATION HERE ===================
    miners_config = [
        {'name': 'BitAxe-Gamma-1', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200},
        {'name': 'BitAxe-Gamma-2', 'ip': '192.168.1.46', 'expected_hashrate_gh': 1150},
        {'name': 'BitAxe-Gamma-3', 'ip': '192.168.1.47', 'expected_hashrate_gh': 1100}
    ]
    # =====================================================================
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create and run the simple monitor
    monitor = SimpleBitAxeMonitor(miners_config, port=8080)
    monitor.run()

if __name__ == '__main__':
    main()
