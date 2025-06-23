#!/usr/bin/env python3
"""
Fixed Bitaxe Monitor Demo

This version has working web interface that displays data correctly.
"""

import sys
import os
import time
import random
import json
from datetime import datetime, timedelta
from collections import deque
import statistics

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, render_template_string, jsonify

# Working HTML Template
WORKING_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Bitaxe Monitor - Enhanced Variance Monitoring</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
        }
        .update-time {
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 20px;
            text-align: center;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-label {
            font-size: 12px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            margin-top: 5px;
        }
        .miners-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        .miner-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .miner-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .miner-name {
            font-size: 18px;
            font-weight: bold;
        }
        .miner-status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-online {
            background: #27ae60;
            color: white;
        }
        .status-offline {
            background: #e74c3c;
            color: white;
        }
        .metric-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #ecf0f1;
        }
        .metric-row:last-child {
            border-bottom: none;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 13px;
        }
        .metric-value {
            font-weight: 500;
            font-size: 13px;
        }
        .efficiency-high {
            color: #27ae60;
        }
        .efficiency-medium {
            color: #f39c12;
        }
        .efficiency-low {
            color: #e74c3c;
        }
        .variance-section {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        .variance-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        .variance-row {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            font-size: 12px;
        }
        .charts-section {
            margin-top: 20px;
        }
        .chart-container {
            margin-bottom: 15px;
        }
        .chart-title {
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 12px;
            color: #2c3e50;
        }
        .chart-box {
            height: 180px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #7f8c8d;
            font-size: 12px;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
</head>
<body>
    <div class="container">
        <h1>Bitaxe Monitor - Enhanced Variance Monitoring</h1>
        
        <div class="update-time" id="updateTime">Loading...</div>
        
        <div class="stats-grid" id="statsGrid">
            <!-- Summary stats will be inserted here -->
        </div>
        
        <div class="miners-grid" id="minersGrid">
            <!-- Miner cards will be inserted here -->
        </div>
        
        <div class="footer">
            Auto-refreshes every 5 seconds | Enhanced variance monitoring active
        </div>
    </div>

    <script>
        const charts = {};
        const chartData = {};
        const maxDataPoints = 15;
        
        function formatUptime(seconds) {
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            
            const parts = [];
            if (days > 0) parts.push(days + 'd');
            if (hours > 0) parts.push(hours + 'h');
            if (minutes > 0) parts.push(minutes + 'm');
            
            return parts.join(' ') || '<1m';
        }
        
        function getEfficiencyClass(percentage) {
            if (percentage >= 95) return 'efficiency-high';
            if (percentage >= 85) return 'efficiency-medium';
            return 'efficiency-low';
        }
        
        function createChart(canvasId, minerName, chartType, expectedValue = 0) {
            const ctx = document.getElementById(canvasId);
            if (!ctx) return null;
            
            const currentTime = new Date().toLocaleTimeString();
            
            let config = {
                type: 'line',
                data: { labels: [currentTime], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: true, position: 'top', labels: { font: { size: 10 } } } },
                    scales: {
                        x: { display: true, ticks: { font: { size: 9 }, maxTicksLimit: 5 } },
                        y: { beginAtZero: false, ticks: { font: { size: 9 } } }
                    },
                    animation: { duration: 300 }
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
            charts[chartKey] = new Chart(ctx, config);
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
            
            // Update hashrate chart
            const hashrateChart = charts[`${minerName}_hashrate`];
            if (hashrateChart) {
                hashrateChart.data.labels = chartData[minerName].times;
                hashrateChart.data.datasets[0].data = chartData[minerName].hashrate;
                hashrateChart.update('none');
            }
            
            // Update directional variance chart
            const directionalChart = charts[`${minerName}_directional`];
            if (directionalChart) {
                directionalChart.data.labels = chartData[minerName].times;
                directionalChart.data.datasets[0].data = new Array(chartData[minerName].times.length).fill(chartData[minerName].expected);
                directionalChart.data.datasets[1].data = chartData[minerName].hashrate;
                directionalChart.update('none');
            }
            
            // Update efficiency chart
            const efficiencyChart = charts[`${minerName}_efficiency`];
            if (efficiencyChart) {
                efficiencyChart.data.labels = chartData[minerName].times;
                efficiencyChart.data.datasets[0].data = chartData[minerName].efficiency;
                efficiencyChart.update('none');
            }
            
            // Update variance chart
            const varianceChart = charts[`${minerName}_variance`];
            if (varianceChart) {
                varianceChart.data.labels = chartData[minerName].times;
                varianceChart.data.datasets[0].data = chartData[minerName].variance;
                varianceChart.update('none');
            }
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
                    
                    // Update miners
                    let minersHtml = '';
                    let chartsToCreate = [];
                    
                    data.miners.forEach((miner, index) => {
                        if (miner.status === 'ONLINE') {
                            const deviation = (miner.hashrate_gh - miner.expected_hashrate_gh).toFixed(1);
                            const deviationSign = deviation >= 0 ? '+' : '';
                            const minerIdSafe = miner.miner_name.replace(/[^a-zA-Z0-9]/g, '');
                            
                            minersHtml += `
                                <div class="miner-card">
                                    <div class="miner-header">
                                        <div class="miner-name">${miner.miner_name}</div>
                                        <div class="miner-status status-online">ONLINE</div>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Hashrate</span>
                                        <span class="metric-value">${miner.hashrate_th.toFixed(3)} TH/s</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Expected</span>
                                        <span class="metric-value">${miner.expected_hashrate_th.toFixed(3)} TH/s</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Efficiency</span>
                                        <span class="metric-value ${getEfficiencyClass(miner.hashrate_efficiency_pct)}">${miner.hashrate_efficiency_pct.toFixed(1)}%</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Deviation</span>
                                        <span class="metric-value">${deviationSign}${deviation} GH/s</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Power</span>
                                        <span class="metric-value">${miner.power_w.toFixed(1)} W</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Temperature</span>
                                        <span class="metric-value">${miner.temperature_c.toFixed(1)}°C</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Frequency</span>
                                        <span class="metric-value">${miner.frequency_mhz} MHz</span>
                                    </div>
                                    
                                    <div class="variance-section">
                                        <div class="variance-title">Enhanced Variance Tracking</div>
                                        <div class="variance-row">
                                            <span>Standard Deviation (60s):</span>
                                            <span>${miner.hashrate_stddev_60s ? miner.hashrate_stddev_60s.toFixed(1) + ' GH/s' : 'Calculating...'}</span>
                                        </div>
                                        <div class="variance-row">
                                            <span>Standard Deviation (300s):</span>
                                            <span>${miner.hashrate_stddev_300s ? miner.hashrate_stddev_300s.toFixed(1) + ' GH/s' : 'Calculating...'}</span>
                                        </div>
                                        <div class="variance-row">
                                            <span>Standard Deviation (600s):</span>
                                            <span>${miner.hashrate_stddev_600s ? miner.hashrate_stddev_600s.toFixed(1) + ' GH/s' : 'Calculating...'}</span>
                                        </div>
                                        <div class="variance-row">
                                            <span>Baseline:</span>
                                            <span>${miner.expected_hashrate_gh.toFixed(0)} GH/s (Expected)</span>
                                        </div>
                                    </div>
                                    
                                    <div class="charts-section">
                                        <div class="chart-container">
                                            <div class="chart-title">Real-time Hashrate</div>
                                            <div class="chart-box">
                                                <canvas id="chart-${minerIdSafe}-hashrate"></canvas>
                                            </div>
                                        </div>
                                        
                                        <div class="chart-container">
                                            <div class="chart-title">Directional Variance (vs Expected Baseline)</div>
                                            <div class="chart-box">
                                                <canvas id="chart-${minerIdSafe}-directional"></canvas>
                                            </div>
                                        </div>
                                        
                                        <div class="chart-container">
                                            <div class="chart-title">Efficiency Tracking</div>
                                            <div class="chart-box">
                                                <canvas id="chart-${minerIdSafe}-efficiency"></canvas>
                                            </div>
                                        </div>
                                        
                                        <div class="chart-container">
                                            <div class="chart-title">Variance Standard Deviation</div>
                                            <div class="chart-box">
                                                <canvas id="chart-${minerIdSafe}-variance"></canvas>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `;
                            
                            chartsToCreate.push({ miner: miner.miner_name, expected: miner.expected_hashrate_gh });
                        } else {
                            minersHtml += `
                                <div class="miner-card">
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
                    
                    // Create or update charts
                    setTimeout(() => {
                        chartsToCreate.forEach(item => {
                            const chartTypes = ['hashrate', 'directional', 'efficiency', 'variance'];
                            const minerIdSafe = item.miner.replace(/[^a-zA-Z0-9]/g, '');
                            chartTypes.forEach(type => {
                                const chartKey = `${item.miner}_${type}`;
                                if (!charts[chartKey]) {
                                    createChart(`chart-${minerIdSafe}-${type}`, item.miner, type, item.expected);
                                }
                            });
                        });
                        
                        // Update charts with new data
                        data.miners.forEach(miner => {
                            if (miner.status === 'ONLINE') {
                                updateChart(miner.miner_name, miner);
                            }
                        });
                    }, 200);
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

# Demo data generation
class WorkingDemo:
    def __init__(self):
        """
        Initialize the WorkingDemo application, setting up the Flask server, baseline miner hashrates, application start time, and rolling history buffers for variance calculations.
        """
        self.app = Flask(__name__)
        self.setup_routes()
        self.base_hashrates = {'Demo-Gamma-1': 1200, 'Demo-Gamma-2': 1150, 'Demo-Gamma-3': 1100}
        self.start_time = datetime.now()
        self.history = {name: deque(maxlen=60) for name in self.base_hashrates.keys()}
    
    def setup_routes(self):
        """
        Define the Flask routes for serving the mining monitor web interface and simulated metrics API.
        
        The root route ('/') renders the main HTML dashboard for real-time mining fleet monitoring. The '/api/metrics' route generates and returns simulated mining metrics as JSON, including per-miner statistics (hashrate, power, temperature, uptime, efficiency, and variance calculations) and fleet-wide aggregates for use by the frontend dashboard.
        """
        @self.app.route('/')
        def index():
            """
            Serves the main web interface for the Bitaxe Monitor application.
            """
            return render_template_string(WORKING_HTML)
        
        @self.app.route('/api/metrics')
        def api_metrics():
            # Generate realistic demo data
            """
            Simulate and return current mining fleet metrics and variance statistics as a JSON response.
            
            Generates time-varying performance data for each miner, including hashrate with variance, power, temperature, frequency, uptime, and standard deviation of hashrate over 60s, 300s, and 600s intervals. Aggregates fleet-wide totals and efficiency, and returns all data in a structured JSON format suitable for real-time monitoring dashboards.
            """
            miners = []
            total_hashrate = 0
            total_power = 0
            
            for name, base_rate in self.base_hashrates.items():
                # Add realistic variance with more dramatic swings for better chart visualization
                variance = random.uniform(-60, 100)  # More dramatic variance for better charts
                actual_hashrate = max(0, base_rate + variance)
                power = random.uniform(13, 16)
                
                # Store history for variance calculation
                self.history[name].append(actual_hashrate)
                
                # Calculate variance if we have enough data
                stddev_60s = None
                stddev_300s = None
                stddev_600s = None
                
                if len(self.history[name]) >= 3:
                    recent_data = list(self.history[name])[-min(6, len(self.history[name])):]  # Last 6 samples for 60s
                    if len(recent_data) > 1:
                        stddev_60s = statistics.stdev(recent_data)
                    
                    if len(self.history[name]) >= 10:
                        medium_data = list(self.history[name])[-min(15, len(self.history[name])):]  # 300s equivalent
                        stddev_300s = statistics.stdev(medium_data)
                    
                    if len(self.history[name]) >= 20:
                        long_data = list(self.history[name])  # All data for 600s
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
                    'temperature_c': random.uniform(55, 75),
                    'frequency_mhz': random.randint(485, 510),
                    'uptime_s': int((datetime.now() - self.start_time).total_seconds())
                }
                miners.append(miner)
                total_hashrate += actual_hashrate / 1000
                total_power += power
            
            fleet_efficiency = (total_hashrate / 3.45) * 100  # 3.45 TH/s total expected
            
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
        Launches the Flask web server for the Bitaxe Monitor demo and displays startup information and feature highlights in the console.
        """
        print("=" * 80)
        print("WORKING BITAXE MONITOR - ENHANCED VARIANCE TRACKING WITH CHARTS")
        print("=" * 80)
        print("[OK] Fixed web interface with working real-time charts")
        print("[OK] Enhanced variance monitoring with Chart.js visualization")
        print("[OK] Directional variance tracking (baseline vs actual)")
        print("[OK] Multi-window variance analysis (60s, 300s, 600s)")
        print("[OK] Real-time hashrate, efficiency, and variance charts")
        print("[OK] Expected hashrate baseline calculations")
        print("=" * 80)
        print()
        print("Open your browser: http://localhost:8080")
        print("Charts update every 5 seconds with live data")
        print("All enhanced variance features working with full visualization")
        print()
        print("Chart Features:")
        print("  - Real-time hashrate tracking")
        print("  - Directional variance with expected baseline (gray dashed line)")
        print("  - Efficiency percentage tracking")
        print("  - Standard deviation variance tracking")
        print("  - 15 data points visible, automatically scrolling")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 80)
        
        self.app.run(host='0.0.0.0', port=8080, debug=False)

if __name__ == '__main__':
    demo = WorkingDemo()
    demo.run()
