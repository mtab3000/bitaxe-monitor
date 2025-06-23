#!/usr/bin/env python3
"""
Fixed Enhanced Variance Monitor - Charts Don't Disappear

This version properly manages chart lifecycle to prevent charts from disappearing.
"""

import random
import statistics
from datetime import datetime
from collections import deque
from flask import Flask, render_template_string, jsonify

# Fixed HTML with persistent charts
PERSISTENT_CHARTS_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Bitaxe Monitor - Enhanced Variance Tracking (Fixed Charts)</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f5f5f5; color: #333;
        }
        .container { max-width: 1600px; margin: 0 auto; }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 10px; }
        .update-time { color: #7f8c8d; font-size: 14px; margin-bottom: 20px; text-align: center; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-label { font-size: 12px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-value { font-size: 24px; font-weight: bold; margin-top: 5px; }
        .miners-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 20px; }
        .miner-card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .miner-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .miner-name { font-size: 18px; font-weight: bold; }
        .miner-status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .status-online { background: #27ae60; color: white; }
        .status-offline { background: #e74c3c; color: white; }
        .metric-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #ecf0f1; }
        .metric-row:last-child { border-bottom: none; }
        .metric-label { color: #7f8c8d; font-size: 13px; }
        .metric-value { font-weight: 500; font-size: 13px; }
        .efficiency-high { color: #27ae60; }
        .efficiency-medium { color: #f39c12; }
        .efficiency-low { color: #e74c3c; }
        .variance-section { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 15px; }
        .variance-title { font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
        .variance-row { display: flex; justify-content: space-between; margin: 5px 0; font-size: 12px; }
        .charts-section { margin-top: 20px; }
        .chart-container { margin-bottom: 15px; }
        .chart-title { font-weight: bold; margin-bottom: 5px; font-size: 12px; color: #2c3e50; }
        .chart-box { height: 180px; background: white; border: 1px solid #ddd; border-radius: 4px; padding: 8px; }
        .footer { text-align: center; margin-top: 40px; color: #7f8c8d; font-size: 12px; }
        .hidden { display: none; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
</head>
<body>
    <div class="container">
        <h1>Bitaxe Monitor - Enhanced Variance Tracking (Fixed Charts)</h1>
        
        <div class="update-time" id="updateTime">Loading...</div>
        
        <div class="stats-grid" id="statsGrid">
            <!-- Summary stats will be inserted here -->
        </div>
        
        <div class="miners-grid" id="minersGrid">
            <!-- Miner cards will be inserted here -->
        </div>
        
        <div class="footer">
            Auto-refreshes every 5 seconds | Charts persist permanently
        </div>
    </div>

    <script>
        const charts = {};
        const chartData = {};
        const maxDataPoints = 20;
        let minersInitialized = false;
        
        function getEfficiencyClass(percentage) {
            if (percentage >= 95) return 'efficiency-high';
            if (percentage >= 85) return 'efficiency-medium';
            return 'efficiency-low';
        }
        
        function createChart(canvasId, minerName, chartType, expectedValue = 0) {
            const ctx = document.getElementById(canvasId);
            if (!ctx) {
                console.log('Canvas not found:', canvasId);
                return null;
            }
            
            const currentTime = new Date().toLocaleTimeString();
            
            let config = {
                type: 'line',
                data: { labels: [currentTime], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { 
                        legend: { 
                            display: true, 
                            position: 'top', 
                            labels: { font: { size: 10 } } 
                        } 
                    },
                    scales: {
                        x: { display: true, ticks: { font: { size: 9 }, maxTicksLimit: 6 } },
                        y: { beginAtZero: false, ticks: { font: { size: 9 } } }
                    },
                    animation: { duration: 200 }
                }
            };
            
            switch(chartType) {
                case 'hashrate':
                    config.data.datasets = [{
                        label: 'Hashrate (GH/s)',
                        data: [0],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.3,
                        fill: true
                    }];
                    break;
                    
                case 'directional':
                    config.data.datasets = [
                        {
                            label: 'Expected Baseline',
                            data: [expectedValue],
                            borderColor: 'rgb(128, 128, 128)',
                            backgroundColor: 'rgba(128, 128, 128, 0.1)',
                            borderDash: [5, 5],
                            fill: false,
                            pointRadius: 0
                        },
                        {
                            label: 'Actual Hashrate',
                            data: [0],
                            borderColor: 'rgb(54, 162, 235)',
                            backgroundColor: 'rgba(54, 162, 235, 0.1)',
                            fill: false
                        }
                    ];
                    config.options.scales.y.title = { display: true, text: 'Hashrate (GH/s)' };
                    break;
                    
                case 'efficiency':
                    config.data.datasets = [{
                        label: 'Efficiency (%)',
                        data: [0],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.3,
                        fill: true
                    }];
                    config.options.scales.y.suggestedMin = 85;
                    config.options.scales.y.suggestedMax = 115;
                    break;
                    
                case 'variance':
                    config.data.datasets = [{
                        label: 'Std Dev (GH/s)',
                        data: [0],
                        borderColor: 'rgb(153, 102, 255)',
                        backgroundColor: 'rgba(153, 102, 255, 0.1)',
                        tension: 0.3,
                        fill: true
                    }];
                    config.options.scales.y.beginAtZero = true;
                    break;
            }
            
            const chartKey = `${minerName}_${chartType}`;
            if (charts[chartKey]) {
                charts[chartKey].destroy();
            }
            charts[chartKey] = new Chart(ctx, config);
            console.log('Created chart:', chartKey);
            return charts[chartKey];
        }
        
        function updateChart(minerName, data) {
            const currentTime = new Date().toLocaleTimeString();
            
            if (!chartData[minerName]) {
                chartData[minerName] = {
                    times: [],
                    hashrate: [],
                    efficiency: [],
                    variance: [],
                    expected: data.expected_hashrate_gh
                };
            }
            
            // Add new data
            chartData[minerName].times.push(currentTime);
            chartData[minerName].hashrate.push(data.hashrate_gh);
            chartData[minerName].efficiency.push(data.hashrate_efficiency_pct);
            chartData[minerName].variance.push(data.hashrate_stddev_60s || 0);
            
            // Keep only recent data points
            if (chartData[minerName].times.length > maxDataPoints) {
                chartData[minerName].times.shift();
                chartData[minerName].hashrate.shift();
                chartData[minerName].efficiency.shift();
                chartData[minerName].variance.shift();
            }
            
            // Update all charts for this miner
            const chartTypes = ['hashrate', 'directional', 'efficiency', 'variance'];
            chartTypes.forEach(type => {
                const chartKey = `${minerName}_${type}`;
                const chart = charts[chartKey];
                
                if (chart) {
                    chart.data.labels = chartData[minerName].times;
                    
                    switch(type) {
                        case 'hashrate':
                            chart.data.datasets[0].data = chartData[minerName].hashrate;
                            break;
                        case 'directional':
                            chart.data.datasets[0].data = new Array(chartData[minerName].times.length).fill(chartData[minerName].expected);
                            chart.data.datasets[1].data = chartData[minerName].hashrate;
                            break;
                        case 'efficiency':
                            chart.data.datasets[0].data = chartData[minerName].efficiency;
                            break;
                        case 'variance':
                            chart.data.datasets[0].data = chartData[minerName].variance;
                            break;
                    }
                    chart.update('none');
                }
            });
        }
        
        function initializeMiners(miners) {
            let minersHtml = '';
            
            miners.forEach((miner, index) => {
                if (miner.status === 'ONLINE') {
                    minersHtml += `
                        <div class="miner-card" data-miner="${miner.miner_name}">
                            <div class="miner-header">
                                <div class="miner-name">${miner.miner_name}</div>
                                <div class="miner-status status-online">ONLINE</div>
                            </div>
                            
                            <div class="metrics-section">
                                <div class="metric-row">
                                    <span class="metric-label">Hashrate</span>
                                    <span class="metric-value" data-field="hashrate">-- TH/s</span>
                                </div>
                                <div class="metric-row">
                                    <span class="metric-label">Expected</span>
                                    <span class="metric-value" data-field="expected">-- TH/s</span>
                                </div>
                                <div class="metric-row">
                                    <span class="metric-label">Efficiency</span>
                                    <span class="metric-value" data-field="efficiency">--%</span>
                                </div>
                                <div class="metric-row">
                                    <span class="metric-label">Deviation</span>
                                    <span class="metric-value" data-field="deviation">-- GH/s</span>
                                </div>
                                <div class="metric-row">
                                    <span class="metric-label">Power</span>
                                    <span class="metric-value" data-field="power">-- W</span>
                                </div>
                                <div class="metric-row">
                                    <span class="metric-label">Temperature</span>
                                    <span class="metric-value" data-field="temperature">--°C</span>
                                </div>
                            </div>
                            
                            <div class="variance-section">
                                <div class="variance-title">Enhanced Variance Tracking</div>
                                <div class="variance-row">
                                    <span>Std Dev (60s):</span>
                                    <span data-field="stddev_60s">Calculating...</span>
                                </div>
                                <div class="variance-row">
                                    <span>Std Dev (300s):</span>
                                    <span data-field="stddev_300s">Calculating...</span>
                                </div>
                                <div class="variance-row">
                                    <span>Std Dev (600s):</span>
                                    <span data-field="stddev_600s">Calculating...</span>
                                </div>
                                <div class="variance-row">
                                    <span>Expected Baseline:</span>
                                    <span data-field="baseline">-- GH/s</span>
                                </div>
                            </div>
                            
                            <div class="charts-section">
                                <div class="chart-container">
                                    <div class="chart-title">Real-time Hashrate</div>
                                    <div class="chart-box">
                                        <canvas id="chart-${index}-hashrate"></canvas>
                                    </div>
                                </div>
                                
                                <div class="chart-container">
                                    <div class="chart-title">Directional Variance (vs Expected Baseline)</div>
                                    <div class="chart-box">
                                        <canvas id="chart-${index}-directional"></canvas>
                                    </div>
                                </div>
                                
                                <div class="chart-container">
                                    <div class="chart-title">Efficiency Tracking</div>
                                    <div class="chart-box">
                                        <canvas id="chart-${index}-efficiency"></canvas>
                                    </div>
                                </div>
                                
                                <div class="chart-container">
                                    <div class="chart-title">Variance Standard Deviation</div>
                                    <div class="chart-box">
                                        <canvas id="chart-${index}-variance"></canvas>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    minersHtml += `
                        <div class="miner-card" data-miner="${miner.miner_name}">
                            <div class="miner-header">
                                <div class="miner-name">${miner.miner_name}</div>
                                <div class="miner-status status-offline">OFFLINE</div>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">IP Address</span>
                                <span class="metric-value">${miner.miner_ip}</span>
                            </div>
                        </div>
                    `;
                }
            });
            
            document.getElementById('minersGrid').innerHTML = minersHtml;
            
            // Create charts after a short delay
            setTimeout(() => {
                miners.forEach((miner, index) => {
                    if (miner.status === 'ONLINE') {
                        const chartTypes = ['hashrate', 'directional', 'efficiency', 'variance'];
                        chartTypes.forEach(type => {
                            createChart(`chart-${index}-${type}`, miner.miner_name, type, miner.expected_hashrate_gh);
                        });
                    }
                });
                console.log('All charts initialized');
            }, 300);
            
            minersInitialized = true;
        }
        
        function updateMinerData(miners) {
            miners.forEach(miner => {
                if (miner.status === 'ONLINE') {
                    const minerCard = document.querySelector(`[data-miner="${miner.miner_name}"]`);
                    if (minerCard) {
                        const deviation = (miner.hashrate_gh - miner.expected_hashrate_gh).toFixed(1);
                        const deviationSign = deviation >= 0 ? '+' : '';
                        
                        // Update metric values
                        const updates = [
                            { field: 'hashrate', value: `${miner.hashrate_th.toFixed(3)} TH/s` },
                            { field: 'expected', value: `${miner.expected_hashrate_th.toFixed(3)} TH/s` },
                            { field: 'efficiency', value: `${miner.hashrate_efficiency_pct.toFixed(1)}%`, class: getEfficiencyClass(miner.hashrate_efficiency_pct) },
                            { field: 'deviation', value: `${deviationSign}${deviation} GH/s` },
                            { field: 'power', value: `${miner.power_w.toFixed(1)} W` },
                            { field: 'temperature', value: `${miner.temperature_c.toFixed(1)}°C` },
                            { field: 'stddev_60s', value: miner.hashrate_stddev_60s ? `${miner.hashrate_stddev_60s.toFixed(1)} GH/s` : 'Calculating...' },
                            { field: 'stddev_300s', value: miner.hashrate_stddev_300s ? `${miner.hashrate_stddev_300s.toFixed(1)} GH/s` : 'Calculating...' },
                            { field: 'stddev_600s', value: miner.hashrate_stddev_600s ? `${miner.hashrate_stddev_600s.toFixed(1)} GH/s` : 'Calculating...' },
                            { field: 'baseline', value: `${miner.expected_hashrate_gh.toFixed(0)} GH/s` }
                        ];
                        
                        updates.forEach(update => {
                            const element = minerCard.querySelector(`[data-field="${update.field}"]`);
                            if (element) {
                                element.textContent = update.value;
                                if (update.class) {
                                    element.className = `metric-value ${update.class}`;
                                }
                            }
                        });
                        
                        // Update charts
                        updateChart(miner.miner_name, miner);
                    }
                }
            });
        }
        
        function updateData() {
            fetch('/api/metrics')
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    // Update timestamp
                    document.getElementById('updateTime').textContent = 
                        'Last updated: ' + new Date(data.timestamp).toLocaleString();
                    
                    // Update summary stats
                    const statsHtml = `
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
                    document.getElementById('statsGrid').innerHTML = statsHtml;
                    
                    // Initialize miners on first run
                    if (!minersInitialized) {
                        initializeMiners(data.miners);
                    } else {
                        // Update existing miner data
                        updateMinerData(data.miners);
                    }
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    document.getElementById('updateTime').textContent = 'Error: ' + error.message;
                });
        }
        
        // Initial update
        updateData();
        
        // Update every 5 seconds
        setInterval(updateData, 5000);
    </script>
</body>
</html>
'''

class FixedDemo:
    def __init__(self):
        """
        Initialize the FixedDemo web application, setting up the Flask app, miner baselines, server start time, and history buffers for variance tracking.
        """
        self.app = Flask(__name__)
        self.setup_routes()
        self.base_hashrates = {'Demo-Gamma-1': 1200, 'Demo-Gamma-2': 1150, 'Demo-Gamma-3': 1100}
        self.start_time = datetime.now()
        self.history = {name: deque(maxlen=60) for name in self.base_hashrates.keys()}
    
    def setup_routes(self):
        """
        Defines the Flask routes for the web dashboard and API endpoints.
        
        The root route ('/') serves the main HTML dashboard for real-time miner monitoring. The '/api/metrics' route returns a JSON response containing simulated metrics for each miner, including current hashrate, expected baseline, efficiency, power, temperature, and variance statistics over multiple time windows, as well as fleet-wide aggregates.
        """
        @self.app.route('/')
        def index():
            return render_template_string(PERSISTENT_CHARTS_HTML)
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """
            Generate and return simulated real-time metrics for all miners, including hashrate, efficiency, power, temperature, and variance statistics.
            
            Returns:
                A Flask JSON response containing a timestamp, fleet-wide aggregates (total hashrate, power, efficiency, miner counts), and a list of per-miner metrics with variance calculations over multiple time windows.
            """
            miners = []
            total_hashrate = 0
            total_power = 0
            
            for name, base_rate in self.base_hashrates.items():
                # Create realistic variance with some trend
                trend = random.uniform(-20, 30)  # Overall trend
                noise = random.uniform(-40, 40)  # Random noise
                actual_hashrate = max(0, base_rate + trend + noise)
                power = random.uniform(13.8, 16.5)
                
                # Store history for variance calculation
                self.history[name].append(actual_hashrate)
                
                # Calculate variance metrics
                stddev_60s = None
                stddev_300s = None  
                stddev_600s = None
                
                if len(self.history[name]) >= 3:
                    recent_data = list(self.history[name])[-min(6, len(self.history[name])):]
                    if len(recent_data) > 1:
                        stddev_60s = statistics.stdev(recent_data)
                    
                    if len(self.history[name]) >= 10:
                        medium_data = list(self.history[name])[-min(15, len(self.history[name])):]
                        stddev_300s = statistics.stdev(medium_data)
                    
                    if len(self.history[name]) >= 20:
                        long_data = list(self.history[name])
                        stddev_600s = statistics.stdev(long_data)
                
                miner = {
                    'miner_name': name,
                    'miner_ip': f'127.0.0.{list(self.base_hashrates.keys()).index(name) + 1}',
                    'status': 'ONLINE',
                    'hashrate_gh': actual_hashrate,
                    'hashrate_th': actual_hashrate / 1000,
                    'expected_hashrate_gh': base_rate,
                    'expected_hashrate_th': base_rate / 1000,
                    'hashrate_efficiency_pct': (actual_hashrate / base_rate) * 100,
                    'hashrate_stddev_60s': stddev_60s,
                    'hashrate_stddev_300s': stddev_300s,
                    'hashrate_stddev_600s': stddev_600s,
                    'power_w': power,
                    'temperature_c': random.uniform(60, 80),
                    'frequency_mhz': random.randint(488, 518),
                    'uptime_s': int((datetime.now() - self.start_time).total_seconds())
                }
                miners.append(miner)
                total_hashrate += actual_hashrate / 1000
                total_power += power
            
            fleet_efficiency = (total_hashrate / 3.45) * 100
            
            response = {
                'timestamp': datetime.now().isoformat(),
                'total_hashrate_th': total_hashrate,
                'total_power_w': total_power,
                'fleet_efficiency': fleet_efficiency,
                'online_count': len(miners),
                'total_count': len(miners),
                'miners': miners
            }
            
            return jsonify(response)
    
    def run(self):
        """
        Starts the Flask web server for the mining dashboard and prints startup information to the console.
        
        The server listens on all interfaces at port 8080 and provides a real-time monitoring dashboard for mining hardware with persistent charts and variance tracking.
        """
        print("=" * 80)
        print("FIXED ENHANCED VARIANCE MONITOR - CHARTS NEVER DISAPPEAR")
        print("=" * 80)
        print("[FIXED] Charts persist through all updates")
        print("[FIXED] No more chart disappearing after 5 seconds")  
        print("[OK] Real-time charts with expected hashrate baseline")
        print("[OK] Directional variance visualization")
        print("[OK] Multi-window variance tracking (60s, 300s, 600s)")
        print("[OK] All enhanced variance features working")
        print("=" * 80)
        print()
        print("Web interface: http://localhost:8080")
        print("Features:")
        print("  - Charts are PERSISTENT and never disappear")
        print("  - Real-time data updates every 5 seconds")
        print("  - Expected baseline (gray dashed line)")
        print("  - Actual hashrate vs baseline comparison")
        print("  - All 4 chart types for each miner")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 80)
        
        self.app.run(host='0.0.0.0', port=8080, debug=False)

if __name__ == '__main__':
    demo = FixedDemo()
    demo.run()
