#!/usr/bin/env python3
"""
Enhanced BitAxe Monitor - Complete Implementation

Working monitor with advanced charts, variance tracking, and statistical analysis.
"""

import sys
import os
import time
import requests
import statistics
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

# Flask imports
from flask import Flask, render_template_string, jsonify

@dataclass
class MinerConfig:
    """Configuration for a BitAxe miner"""
    name: str
    ip: str
    expected_hashrate_gh: float = 1100

@dataclass  
class MinerMetrics:
    """Enhanced metrics for a BitAxe miner"""
    miner_name: str
    miner_ip: str
    status: str
    hashrate_gh: float = 0
    hashrate_th: float = 0
    expected_hashrate_gh: float = 1100
    expected_hashrate_th: float = 1.1
    hashrate_efficiency_pct: float = 0
    hashrate_stddev_60s: float = 0
    hashrate_stddev_300s: float = 0
    hashrate_stddev_600s: float = 0
    power_w: float = 0
    temperature_c: float = 0
    frequency_mhz: float = 0
    voltage_v: float = 0
    uptime_s: int = 0
    fan_speed_rpm: int = 0
    chip_temp_c: float = 0

class VarianceTracker:
    """Enhanced variance tracking with multiple time windows"""
    
    def __init__(self, window_sizes: List[int] = [60, 300, 600]):
        self.window_sizes = window_sizes  # seconds
        self.data_points = {size: deque(maxlen=size//5) for size in window_sizes}  # 5-second intervals
        self.timestamps = {size: deque(maxlen=size//5) for size in window_sizes}
        
    def add_datapoint(self, value: float, timestamp: datetime):
        """Add a new data point to all tracking windows"""
        for window_size in self.window_sizes:
            self.data_points[window_size].append(value)
            self.timestamps[window_size].append(timestamp)
    
    def get_standard_deviation(self, window_size: int) -> float:
        """Calculate standard deviation for a specific window"""
        if window_size not in self.data_points or len(self.data_points[window_size]) < 2:
            return 0.0
        return statistics.stdev(self.data_points[window_size])
    
    def get_mean(self, window_size: int) -> float:
        """Calculate mean for a specific window"""
        if window_size not in self.data_points or len(self.data_points[window_size]) == 0:
            return 0.0
        return statistics.mean(self.data_points[window_size])
    
    def get_variance_percentage(self, expected_value: float, window_size: int) -> float:
        """Calculate variance percentage from expected value"""
        mean_value = self.get_mean(window_size)
        if expected_value == 0:
            return 0.0
        return ((mean_value - expected_value) / expected_value) * 100
class EnhancedBitAxeMonitor:
    """Enhanced BitAxe monitoring system with variance tracking and charts"""
    
    def __init__(self, miners_config: List[Dict], port: int = 8080):
        self.miners_config = [MinerConfig(**config) for config in miners_config]
        self.port = port
        self.variance_trackers = {miner.name: VarianceTracker() for miner in self.miners_config}
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Historical data storage for charts
        self.chart_data = {}
        for miner in self.miners_config:
            self.chart_data[miner.name] = {
                'timestamps': deque(maxlen=50),  # Store last 50 data points
                'hashrates': deque(maxlen=50),
                'efficiencies': deque(maxlen=50),
                'variances': deque(maxlen=50),
                'std_devs': deque(maxlen=50)
            }
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            return render_template_string(ENHANCED_HTML_TEMPLATE)
            
        @self.app.route('/api/metrics')
        def api_metrics():
            return jsonify(self.get_all_metrics())
    
    def fetch_miner_data(self, miner: MinerConfig) -> Optional[Dict]:
        """Enhanced data fetching with additional metrics"""
        try:
            response = requests.get(f'http://{miner.ip}/api/system/info', timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to fetch data from {miner.name} ({miner.ip}): {e}")
            return None    
    def parse_miner_metrics(self, miner: MinerConfig, data: Dict) -> MinerMetrics:
        """Enhanced parsing with variance calculations"""
        if not data:
            return MinerMetrics(
                miner_name=miner.name,
                miner_ip=miner.ip,
                status='OFFLINE'
            )
        
        # Extract core metrics
        hashrate_gh = data.get('hashRate', 0)
        hashrate_th = hashrate_gh / 1000.0
        expected_hashrate_th = miner.expected_hashrate_gh / 1000.0
        
        # Calculate efficiency
        efficiency_pct = (hashrate_gh / miner.expected_hashrate_gh * 100) if miner.expected_hashrate_gh > 0 else 0
        
        # Update variance tracker
        current_time = datetime.now()
        tracker = self.variance_trackers[miner.name]
        tracker.add_datapoint(hashrate_gh, current_time)
        
        # Update chart data
        chart_data = self.chart_data[miner.name]
        chart_data['timestamps'].append(current_time.strftime('%H:%M:%S'))
        chart_data['hashrates'].append(hashrate_gh)
        chart_data['efficiencies'].append(efficiency_pct)
        chart_data['variances'].append(hashrate_gh - miner.expected_hashrate_gh)
        chart_data['std_devs'].append(tracker.get_standard_deviation(60))
        
        return MinerMetrics(
            miner_name=miner.name,
            miner_ip=miner.ip,
            status='ONLINE',
            hashrate_gh=hashrate_gh,
            hashrate_th=hashrate_th,
            expected_hashrate_gh=miner.expected_hashrate_gh,
            expected_hashrate_th=expected_hashrate_th,
            hashrate_efficiency_pct=efficiency_pct,
            hashrate_stddev_60s=tracker.get_standard_deviation(60),
            hashrate_stddev_300s=tracker.get_standard_deviation(300),
            hashrate_stddev_600s=tracker.get_standard_deviation(600),
            power_w=data.get('power', 0),
            temperature_c=data.get('temp', 0),
            frequency_mhz=data.get('frequency', 0),
            voltage_v=data.get('voltage', 0),
            uptime_s=data.get('uptimeSeconds', 0),
            fan_speed_rpm=data.get('fanSpeed', 0),
            chip_temp_c=data.get('chipTemp', data.get('temp', 0))
        )    
    def get_all_metrics(self) -> Dict:
        """Enhanced metrics collection with fleet statistics"""
        miners_data = []
        total_hashrate_th = 0
        total_power_w = 0
        online_count = 0
        
        for miner in self.miners_config:
            raw_data = self.fetch_miner_data(miner)
            metrics = self.parse_miner_metrics(miner, raw_data)
            miners_data.append(metrics.__dict__)
            
            if metrics.status == 'ONLINE':
                online_count += 1
                total_hashrate_th += metrics.hashrate_th
                total_power_w += metrics.power_w
        
        # Calculate fleet efficiency
        total_expected_th = sum(miner.expected_hashrate_gh for miner in self.miners_config) / 1000.0
        fleet_efficiency = (total_hashrate_th / total_expected_th * 100) if total_expected_th > 0 else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_hashrate_th': total_hashrate_th,
            'total_power_w': total_power_w,
            'fleet_efficiency': fleet_efficiency,
            'online_count': online_count,
            'total_count': len(self.miners_config),
            'miners': miners_data,
            'chart_data': self.chart_data
        }
    
    def run(self):
        """Run the enhanced monitor"""
        logging.info(f"Starting Enhanced BitAxe Monitor on port {self.port}")
        logging.info(f"Monitoring {len(self.miners_config)} miners:")
        for miner in self.miners_config:
            logging.info(f"  - {miner.name} at {miner.ip} (expected: {miner.expected_hashrate_gh} GH/s)")
        
        try:
            self.app.run(host='0.0.0.0', port=self.port, debug=False)
        except KeyboardInterrupt:
            logging.info("Monitor stopped by user")
        except Exception as e:
            logging.error(f"Monitor error: {e}")

# Enhanced HTML Template with 4 charts per miner
ENHANCED_HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced BitAxe Monitor</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; color: #333;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95); padding: 2rem 0; text-align: center;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1); margin-bottom: 2rem;
        }
        
        .header h1 { color: #4a5568; font-size: 2.5rem; font-weight: 300; margin-bottom: 0.5rem; }
        .header .subtitle { color: #718096; font-size: 1.2rem; }
        .container { max-width: 1400px; margin: 0 auto; padding: 0 1rem; }
        
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem; margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95); padding: 1.5rem; border-radius: 12px;
            text-align: center; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover { transform: translateY(-2px); }
        .stat-label { display: block; color: #718096; font-size: 0.9rem; margin-bottom: 0.5rem; }
        .stat-value { font-size: 1.8rem; font-weight: 600; color: #2d3748; }
        
        .miners-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(800px, 1fr)); gap: 2rem; }
        
        .miner-card {
            background: rgba(255, 255, 255, 0.95); border-radius: 16px; overflow: hidden;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12); transition: all 0.3s ease;
        }
        
        .miner-card:hover { transform: translateY(-5px); }
        
        .miner-header {
            background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
            color: white; padding: 1.5rem; display: flex; justify-content: space-between; align-items: center;
        }
        
        .miner-name { font-size: 1.4rem; font-weight: 600; }
        .status { padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 600; }
        .status-online { background: rgba(72, 187, 120, 0.2); color: #2f855a; }
        .status-offline { background: rgba(245, 101, 101, 0.2); color: #c53030; }
        
        .metrics-section {
            padding: 1.5rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem; border-bottom: 1px solid #e2e8f0;
        }
        
        .metric { text-align: center; }
        .metric-label { display: block; color: #718096; font-size: 0.8rem; margin-bottom: 0.5rem; }
        .metric-value { font-size: 1.3rem; font-weight: 600; color: #2d3748; }
        
        .efficiency-excellent { color: #38a169; }
        .efficiency-good { color: #d69e2e; }
        .efficiency-poor { color: #e53e3e; }
        
        .charts-section { padding: 1.5rem; }
        .charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .chart-container { background: #f7fafc; border-radius: 8px; padding: 1rem; height: 250px; }
        .chart-title { font-size: 0.9rem; color: #4a5568; margin-bottom: 0.5rem; text-align: center; }
        
        .update-time { text-align: center; color: #718096; margin-top: 2rem; font-size: 0.9rem; }
        
        @media (max-width: 1200px) {
            .charts-grid { grid-template-columns: 1fr; }
            .miners-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Enhanced BitAxe Monitor</h1>
        <div class="subtitle">Real-time Mining Performance with Variance Analysis</div>
    </div>
    
    <div class="container">
        <div id="statsGrid" class="stats-grid"></div>
        <div id="minersGrid" class="miners-grid"></div>
        <div id="updateTime" class="update-time"></div>
    </div>

    <script>
        const charts = {};
        let isInitialized = false;

        function getEfficiencyClass(efficiency) {
            if (efficiency >= 95) return 'efficiency-excellent';
            if (efficiency >= 85) return 'efficiency-good';
            return 'efficiency-poor';
        }
        function createCharts(minerName, minerIdSafe) {
            const chartConfigs = [
                { id: `hashrate-chart-${minerIdSafe}`, title: 'Hashrate (GH/s)', color: 'rgb(75, 192, 192)', dataKey: 'hashrates' },
                { id: `variance-chart-${minerIdSafe}`, title: 'Directional Variance', color: 'rgb(54, 162, 235)', dataKey: 'variances' },
                { id: `efficiency-chart-${minerIdSafe}`, title: 'Efficiency (%)', color: 'rgb(255, 206, 86)', dataKey: 'efficiencies' },
                { id: `stddev-chart-${minerIdSafe}`, title: 'Standard Deviation', color: 'rgb(153, 102, 255)', dataKey: 'std_devs' }
            ];

            chartConfigs.forEach(config => {
                const ctx = document.getElementById(config.id);
                if (ctx) {
                    charts[config.id] = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: config.title, data: [], borderColor: config.color,
                                backgroundColor: config.color + '20', tension: 0.4, fill: true
                            }]
                        },
                        options: {
                            responsive: true, maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: { y: { beginAtZero: config.dataKey === 'variances' ? false : true } }
                        }
                    });
                }
            });
        }

        function updateCharts(minerName, data) {
            const minerIdSafe = minerName.replace(/[^a-zA-Z0-9]/g, '');
            const minerChartData = data.chart_data[minerName];
            if (!minerChartData) return;

            const chartConfigs = [
                { id: `hashrate-chart-${minerIdSafe}`, dataKey: 'hashrates' },
                { id: `variance-chart-${minerIdSafe}`, dataKey: 'variances' },
                { id: `efficiency-chart-${minerIdSafe}`, dataKey: 'efficiencies' },
                { id: `stddev-chart-${minerIdSafe}`, dataKey: 'std_devs' }
            ];

            chartConfigs.forEach(config => {
                const chart = charts[config.id];
                if (chart && minerChartData[config.dataKey]) {
                    chart.data.labels = Array.from(minerChartData.timestamps);
                    chart.data.datasets[0].data = Array.from(minerChartData[config.dataKey]);
                    chart.update('none');
                }
            });
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
                        <div class="metrics-section" id="metrics-${minerIdSafe}"></div>
                        <div class="charts-section">
                            <div class="charts-grid">
                                <div class="chart-container">
                                    <div class="chart-title">Hashrate (GH/s)</div>
                                    <canvas id="hashrate-chart-${minerIdSafe}"></canvas>
                                </div>
                                <div class="chart-container">
                                    <div class="chart-title">Directional Variance</div>
                                    <canvas id="variance-chart-${minerIdSafe}"></canvas>
                                </div>
                                <div class="chart-container">
                                    <div class="chart-title">Efficiency (%)</div>
                                    <canvas id="efficiency-chart-${minerIdSafe}"></canvas>
                                </div>
                                <div class="chart-container">
                                    <div class="chart-title">Standard Deviation</div>
                                    <canvas id="stddev-chart-${minerIdSafe}"></canvas>
                                </div>
                            </div>
                        </div>
                    `;
                    minersGrid.appendChild(minerCard);
                    setTimeout(() => { createCharts(miner.miner_name, minerIdSafe); }, 100);
                } else {
                    const minerCard = document.createElement('div');
                    minerCard.className = 'miner-card';
                    minerCard.innerHTML = `
                        <div class="miner-header">
                            <div class="miner-name">${miner.miner_name}</div>
                            <div class="status status-offline">OFFLINE</div>
                        </div>
                        <div class="metrics-section">
                            <div class="metric">
                                <span class="metric-label">IP Address</span>
                                <span class="metric-value">${miner.miner_ip}</span>
                            </div>
                        </div>
                    `;
                    minersGrid.appendChild(minerCard);
                }
            });
            isInitialized = true;
        }-value ${getEfficiencyClass(miner.hashrate_efficiency_pct)}">${miner.hashrate_efficiency_pct.toFixed(1)}%</span>
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
                    <div class="metric">
                        <span class="metric-label">StdDev 60s</span>
                        <span class="metric-value">${miner.hashrate_stddev_60s.toFixed(1)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">StdDev 300s</span>
                        <span class="metric-value">${miner.hashrate_stddev_300s.toFixed(1)}</span>
                    </div>
                `;
                updateCharts(miner.miner_name, data);
            }
        }
        
        function updateData() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('updateTime').textContent = 'Last updated: ' + new Date(data.timestamp).toLocaleString();
                    
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
                    
                    if (!isInitialized) {
                        initializeUI(data);
                    } else {
                        data.miners.forEach(miner => {
                            updateMinerData(miner, data);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    document.getElementById('updateTime').textContent = 'Error: ' + error.message;
                });
        }
        
        updateData();
        setInterval(updateData, 5000);
    </script>
</body>
</html>'''

def main():
    """Main function to run the enhanced BitAxe monitor"""
    
    # =================== EDIT YOUR CONFIGURATION HERE ===================
    miners_config = [
        {'name': 'BitAxe-Gamma-1', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200},
        {'name': 'BitAxe-Gamma-2', 'ip': '192.168.1.46', 'expected_hashrate_gh': 1150},
        {'name': 'BitAxe-Gamma-3', 'ip': '192.168.1.47', 'expected_hashrate_gh': 1100}
    ]
    # =====================================================================
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create and run the enhanced monitor
    monitor = EnhancedBitAxeMonitor(miners_config, port=8080)
    monitor.run()

if __name__ == '__main__':
    main()
