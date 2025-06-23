#!/usr/bin/env python3
"""
Enhanced BitAxe Monitor with Working Charts

This is the fixed main monitor that includes all chart functionality
from the working demo, adapted for real BitAxe miners.

To use this monitor:
1. Edit the miners_config section with your actual BitAxe IPs
2. Run: python enhanced_bitaxe_monitor.py
3. Open: http://localhost:8080

Features:
- Real-time hashrate charts
- Directional variance tracking with baseline
- Multi-window variance analysis (60s, 300s, 600s)
- Efficiency and standard deviation monitoring
- Professional web interface with Chart.js
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
    expected_hashrate_gh: float = 1100  # Default expected hashrate

@dataclass  
class MinerMetrics:
    """Metrics for a BitAxe miner"""
    miner_name: str
    miner_ip: str
    status: str
    hashrate_gh: float = 0
    hashrate_th: float = 0
    expected_hashrate_gh: float = 1100
    expected_hashrate_th: float = 1.1
    hashrate_efficiency_pct: float = 0
    hashrate_stddev_60s: Optional[float] = None
    hashrate_stddev_300s: Optional[float] = None
    hashrate_stddev_600s: Optional[float] = None
    power_w: float = 0
    temperature_c: float = 0
    frequency_mhz: int = 0
    uptime_s: int = 0

class BitAxeAPI:
    """API client for communicating with BitAxe miners"""
    
    def __init__(self, timeout=5):
        self.timeout = timeout
    
    def get_system_info(self, miner_config: MinerConfig) -> Optional[Dict]:
        """Get system info from a BitAxe miner"""
        try:
            url = f"http://{miner_config.ip}/api/system/info"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.warning(f"Failed to get data from {miner_config.name} ({miner_config.ip}): Status {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"Connection error to {miner_config.name} ({miner_config.ip}): {e}")
            return None

class VarianceTracker:
    """Tracks variance data for multiple time windows"""
    
    def __init__(self, maxlen=600):  # 10 minutes of data at 1-second intervals
        self.data = deque(maxlen=maxlen)
        self.timestamps = deque(maxlen=maxlen)
    
    def add_data_point(self, value: float):
        """Add a new data point"""
        self.data.append(value)
        self.timestamps.append(datetime.now())
    
    def get_variance_stats(self, window_seconds: int) -> Optional[float]:
        """Get standard deviation for a specific time window"""
        if len(self.data) < 2:
            return None
        
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        
        # Filter data points within the time window
        recent_data = []
        for i, timestamp in enumerate(self.timestamps):
            if timestamp >= cutoff_time:
                recent_data.append(self.data[i])
        
        if len(recent_data) < 2:
            return None
        
        return statistics.stdev(recent_data)

class EnhancedBitAxeMonitor:
    """Enhanced BitAxe monitor with variance tracking and charts"""
    
    def __init__(self, miners_config: List[Dict], port=8080):
        self.app = Flask(__name__)
        self.miners = [MinerConfig(**config) for config in miners_config]
        self.api = BitAxeAPI()
        self.port = port
        
        # Variance tracking for each miner
        self.variance_trackers = {miner.name: VarianceTracker() for miner in self.miners}
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template_string(ENHANCED_HTML_TEMPLATE)
        
        @self.app.route('/api/metrics')
        def api_metrics():
            return jsonify(self.get_all_metrics())
    
    def get_miner_metrics(self, miner: MinerConfig) -> MinerMetrics:
        """Get metrics for a single miner"""
        
        # Get data from BitAxe API
        system_info = self.api.get_system_info(miner)
        
        if system_info is None:
            # Miner is offline
            return MinerMetrics(
                miner_name=miner.name,
                miner_ip=miner.ip,
                status='OFFLINE'
            )
        
        # Extract metrics from system info
        hashrate_gh = system_info.get('hashRate', 0)  # GH/s
        power_w = system_info.get('power', 0)
        temperature_c = system_info.get('temp', 0)
        frequency_mhz = system_info.get('frequency', 0)
        uptime_s = system_info.get('uptimeSeconds', 0)
        
        # Calculate efficiency
        expected_hashrate = miner.expected_hashrate_gh
        efficiency_pct = (hashrate_gh / expected_hashrate) * 100 if expected_hashrate > 0 else 0
        
        # Track variance
        tracker = self.variance_trackers[miner.name]
        tracker.add_data_point(hashrate_gh)
        
        # Calculate variance for different time windows
        stddev_60s = tracker.get_variance_stats(60)
        stddev_300s = tracker.get_variance_stats(300)
        stddev_600s = tracker.get_variance_stats(600)
        
        return MinerMetrics(
            miner_name=miner.name,
            miner_ip=miner.ip,
            status='ONLINE',
            hashrate_gh=hashrate_gh,
            hashrate_th=hashrate_gh / 1000,
            expected_hashrate_gh=expected_hashrate,
            expected_hashrate_th=expected_hashrate / 1000,
            hashrate_efficiency_pct=efficiency_pct,
            hashrate_stddev_60s=stddev_60s,
            hashrate_stddev_300s=stddev_300s,
            hashrate_stddev_600s=stddev_600s,
            power_w=power_w,
            temperature_c=temperature_c,
            frequency_mhz=frequency_mhz,
            uptime_s=uptime_s
        )
    
    def get_all_metrics(self) -> Dict:
        """Get metrics for all miners"""
        
        miners_data = []
        total_hashrate_th = 0
        total_power_w = 0
        online_count = 0
        
        for miner in self.miners:
            metrics = self.get_miner_metrics(miner)
            
            # Convert to dict for JSON serialization
            miner_dict = {
                'miner_name': metrics.miner_name,
                'miner_ip': metrics.miner_ip,
                'status': metrics.status,
                'hashrate_gh': metrics.hashrate_gh,
                'hashrate_th': metrics.hashrate_th,
                'expected_hashrate_gh': metrics.expected_hashrate_gh,
                'expected_hashrate_th': metrics.expected_hashrate_th,
                'hashrate_efficiency_pct': metrics.hashrate_efficiency_pct,
                'hashrate_stddev_60s': metrics.hashrate_stddev_60s,
                'hashrate_stddev_300s': metrics.hashrate_stddev_300s,
                'hashrate_stddev_600s': metrics.hashrate_stddev_600s,
                'power_w': metrics.power_w,
                'temperature_c': metrics.temperature_c,
                'frequency_mhz': metrics.frequency_mhz,
                'uptime_s': metrics.uptime_s
            }
            
            miners_data.append(miner_dict)
            
            if metrics.status == 'ONLINE':
                online_count += 1
                total_hashrate_th += metrics.hashrate_th
                total_power_w += metrics.power_w
        
        # Calculate fleet efficiency
        total_expected_th = sum(miner.expected_hashrate_gh for miner in self.miners) / 1000
        fleet_efficiency = (total_hashrate_th / total_expected_th) * 100 if total_expected_th > 0 else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_hashrate_th': total_hashrate_th,
            'total_power_w': total_power_w,
            'fleet_efficiency': fleet_efficiency,
            'online_count': online_count,
            'total_count': len(self.miners),
            'miners': miners_data
        }
    
    def run(self):
        """Run the enhanced monitor"""
        print("=" * 80)
        print("ENHANCED BITAXE MONITOR - WITH WORKING CHARTS")
        print("=" * 80)
        print("[OK] Real-time charts with Chart.js visualization")
        print("[OK] Directional variance tracking (baseline vs actual)")
        print("[OK] Multi-window variance analysis (60s, 300s, 600s)")
        print("[OK] Expected hashrate baseline calculations")
        print("[OK] Professional web interface")
        print("=" * 80)
        print()
        print(f"Monitoring {len(self.miners)} BitAxe miners:")
        for miner in self.miners:
            print(f"  - {miner.name} ({miner.ip}) - Expected: {miner.expected_hashrate_gh} GH/s")
        print()
        print(f"Web interface: http://localhost:{self.port}")
        print("Charts update every 5 seconds with live data")
        print("All enhanced variance features working")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 80)
        
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

# Enhanced HTML Template with Chart.js - THIS IS WHERE THE MAGIC HAPPENS
ENHANCED_HTML_TEMPLATE = '''<!DOCTYPE html>
<html><head>
    <title>BitAxe Monitor - Enhanced Variance Tracking</title>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; color: #333; }
        .container { max-width: 1600px; margin: 0 auto; }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 10px; }
        .update-time { color: #7f8c8d; font-size: 14px; margin-bottom: 20px; text-align: center; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-label { font-size: 12px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-value { font-size: 24px; font-weight: bold; margin-top: 5px; }
        .miners-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
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
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
</head><body>
    <div class="container">
        <h1>BitAxe Monitor - Enhanced Variance Tracking</h1>
        <div class="update-time" id="updateTime">Loading...</div>
        <div class="stats-grid" id="statsGrid"></div>
        <div class="miners-grid" id="minersGrid"></div>
        <div class="footer">Auto-refreshes every 5 seconds | Enhanced variance monitoring active</div>
    </div>

    <script>
        const charts = {}; const chartData = {}; const maxDataPoints = 15;
        
        function getEfficiencyClass(percentage) {
            if (percentage >= 95) return 'efficiency-high';
            if (percentage >= 85) return 'efficiency-medium';
            return 'efficiency-low';
        }
        
        function createChart(canvasId, minerName, chartType, expectedValue = 0) {
            const ctx = document.getElementById(canvasId);
            if (!ctx) return null;
            
            let config = {
                type: 'line',
                data: { labels: [new Date().toLocaleTimeString()], datasets: [] },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: true, position: 'top', labels: { font: { size: 10 } } } },
                    scales: { x: { ticks: { font: { size: 9 }, maxTicksLimit: 5 } }, y: { ticks: { font: { size: 9 } } } },
                    animation: { duration: 300 }
                }
            };
            
            switch(chartType) {
                case 'hashrate':
                    config.data.datasets = [{ label: 'Hashrate (GH/s)', data: [0], borderColor: 'rgb(75, 192, 192)', backgroundColor: 'rgba(75, 192, 192, 0.1)', tension: 0.3, fill: true }];
                    break;
                case 'directional':
                    config.data.datasets = [
                        { label: 'Expected Baseline', data: [expectedValue], borderColor: 'rgb(128, 128, 128)', borderDash: [5, 5], fill: false, pointRadius: 0 },
                        { label: 'Actual Hashrate', data: [0], borderColor: 'rgb(54, 162, 235)', fill: false }
                    ];
                    break;
                case 'efficiency':
                    config.data.datasets = [{ label: 'Efficiency (%)', data: [0], borderColor: 'rgb(255, 99, 132)', backgroundColor: 'rgba(255, 99, 132, 0.1)', tension: 0.3, fill: true }];
                    config.options.scales.y.suggestedMin = 85; config.options.scales.y.suggestedMax = 115;
                    break;
                case 'variance':
                    config.data.datasets = [{ label: 'Std Dev (GH/s)', data: [0], borderColor: 'rgb(153, 102, 255)', backgroundColor: 'rgba(153, 102, 255, 0.1)', tension: 0.3, fill: true }];
                    config.options.scales.y.beginAtZero = true;
                    break;
            }
            
            const chartKey = minerName + '_' + chartType;
            charts[chartKey] = new Chart(ctx, config);
            return charts[chartKey];
        }
        
        function updateChart(minerName, data) {
            const currentTime = new Date().toLocaleTimeString();
            
            if (!chartData[minerName]) {
                chartData[minerName] = { times: [], hashrate: [], efficiency: [], variance: [], expected: data.expected_hashrate_gh };
            }
            
            chartData[minerName].times.push(currentTime);
            chartData[minerName].hashrate.push(data.hashrate_gh);
            chartData[minerName].efficiency.push(data.hashrate_efficiency_pct);
            chartData[minerName].variance.push(data.hashrate_stddev_60s || 0);
            
            if (chartData[minerName].times.length > maxDataPoints) {
                chartData[minerName].times.shift(); chartData[minerName].hashrate.shift();
                chartData[minerName].efficiency.shift(); chartData[minerName].variance.shift();
            }
            
            ['hashrate', 'directional', 'efficiency', 'variance'].forEach(type => {
                const chart = charts[minerName + '_' + type];
                if (chart) {
                    chart.data.labels = chartData[minerName].times;
                    if (type === 'hashrate') chart.data.datasets[0].data = chartData[minerName].hashrate;
                    else if (type === 'directional') {
                        chart.data.datasets[0].data = new Array(chartData[minerName].times.length).fill(chartData[minerName].expected);
                        chart.data.datasets[1].data = chartData[minerName].hashrate;
                    }
                    else if (type === 'efficiency') chart.data.datasets[0].data = chartData[minerName].efficiency;
                    else if (type === 'variance') chart.data.datasets[0].data = chartData[minerName].variance;
                    chart.update('none');
                }
            });
        }
        
        let isInitialized = false;
        
        function initializeUI(data) {
            document.getElementById('minersGrid').innerHTML = '';
            
            data.miners.forEach(miner => {
                if (miner.status === 'ONLINE') {
                    const minerIdSafe = miner.miner_name.replace(/[^a-zA-Z0-9]/g, '');
                    const minerCard = document.createElement('div');
                    minerCard.className = 'miner-card';
                    minerCard.id = 'miner-card-' + minerIdSafe;
                    
                    minerCard.innerHTML = 
                        '<div class="miner-header"><div class="miner-name">' + miner.miner_name + '</div><div class="miner-status status-online" id="status-' + minerIdSafe + '">ONLINE</div></div>' +
                        '<div id="metrics-' + minerIdSafe + '"></div>' +
                        '<div class="variance-section" id="variance-' + minerIdSafe + '"></div>' +
                        '<div class="charts-section">' +
                        '<div class="chart-container"><div class="chart-title">Real-time Hashrate</div><div class="chart-box"><canvas id="chart-' + minerIdSafe + '-hashrate"></canvas></div></div>' +
                        '<div class="chart-container"><div class="chart-title">Directional Variance (vs Expected Baseline)</div><div class="chart-box"><canvas id="chart-' + minerIdSafe + '-directional"></canvas></div></div>' +
                        '<div class="chart-container"><div class="chart-title">Efficiency Tracking</div><div class="chart-box"><canvas id="chart-' + minerIdSafe + '-efficiency"></canvas></div></div>' +
                        '<div class="chart-container"><div class="chart-title">Variance Standard Deviation</div><div class="chart-box"><canvas id="chart-' + minerIdSafe + '-variance"></canvas></div></div>' +
                        '</div>';
                    
                    document.getElementById('minersGrid').appendChild(minerCard);
                    
                    // Create charts for this miner
                    setTimeout(() => {
                        ['hashrate', 'directional', 'efficiency', 'variance'].forEach(type => {
                            createChart('chart-' + minerIdSafe + '-' + type, miner.miner_name, type, miner.expected_hashrate_gh);
                        });
                    }, 100);
                } else {
                    const minerIdSafe = miner.miner_name.replace(/[^a-zA-Z0-9]/g, '');
                    const minerCard = document.createElement('div');
                    minerCard.className = 'miner-card';
                    minerCard.id = 'miner-card-' + minerIdSafe;
                    
                    minerCard.innerHTML = 
                        '<div class="miner-header"><div class="miner-name">' + miner.miner_name + '</div><div class="miner-status status-offline" id="status-' + minerIdSafe + '">OFFLINE</div></div>' +
                        '<div class="metric-row"><span class="metric-label">IP Address</span><span class="metric-value">' + miner.miner_ip + '</span></div>';
                    
                    document.getElementById('minersGrid').appendChild(minerCard);
                }
            });
            
            isInitialized = true;
        }
        
        function updateMinerData(miner) {
            const minerIdSafe = miner.miner_name.replace(/[^a-zA-Z0-9]/g, '');
            const statusElement = document.getElementById('status-' + minerIdSafe);
            const metricsElement = document.getElementById('metrics-' + minerIdSafe);
            const varianceElement = document.getElementById('variance-' + minerIdSafe);
            
            if (miner.status === 'ONLINE') {
                if (statusElement) {
                    statusElement.textContent = 'ONLINE';
                    statusElement.className = 'miner-status status-online';
                }
                
                if (metricsElement) {
                    const deviation = (miner.hashrate_gh - miner.expected_hashrate_gh).toFixed(1);
                    const deviationSign = deviation >= 0 ? '+' : '';
                    
                    metricsElement.innerHTML = 
                        '<div class="metric-row"><span class="metric-label">Hashrate</span><span class="metric-value">' + miner.hashrate_th.toFixed(3) + ' TH/s</span></div>' +
                        '<div class="metric-row"><span class="metric-label">Expected</span><span class="metric-value">' + miner.expected_hashrate_th.toFixed(3) + ' TH/s</span></div>' +
                        '<div class="metric-row"><span class="metric-label">Efficiency</span><span class="metric-value ' + getEfficiencyClass(miner.hashrate_efficiency_pct) + '">' + miner.hashrate_efficiency_pct.toFixed(1) + '%</span></div>' +
                        '<div class="metric-row"><span class="metric-label">Deviation</span><span class="metric-value">' + deviationSign + deviation + ' GH/s</span></div>' +
                        '<div class="metric-row"><span class="metric-label">Power</span><span class="metric-value">' + miner.power_w.toFixed(1) + ' W</span></div>' +
                        '<div class="metric-row"><span class="metric-label">Temperature</span><span class="metric-value">' + miner.temperature_c.toFixed(1) + '°C</span></div>';
                }
                
                if (varianceElement) {
                    varianceElement.innerHTML = 
                        '<div class="variance-title">Enhanced Variance Tracking</div>' +
                        '<div class="variance-row"><span>Std Dev (60s):</span><span>' + (miner.hashrate_stddev_60s ? miner.hashrate_stddev_60s.toFixed(1) + ' GH/s' : 'Calculating...') + '</span></div>' +
                        '<div class="variance-row"><span>Std Dev (300s):</span><span>' + (miner.hashrate_stddev_300s ? miner.hashrate_stddev_300s.toFixed(1) + ' GH/s' : 'Calculating...') + '</span></div>' +
                        '<div class="variance-row"><span>Std Dev (600s):</span><span>' + (miner.hashrate_stddev_600s ? miner.hashrate_stddev_600s.toFixed(1) + ' GH/s' : 'Calculating...') + '</span></div>' +
                        '<div class="variance-row"><span>Expected Baseline:</span><span>' + miner.expected_hashrate_gh.toFixed(0) + ' GH/s</span></div>';
                }
                
                updateChart(miner.miner_name, miner);
            } else {
                if (statusElement) {
                    statusElement.textContent = 'OFFLINE';
                    statusElement.className = 'miner-status status-offline';
                }
            }
        }
        
        function updateData() {
            fetch('/api/metrics').then(response => response.json()).then(data => {
                document.getElementById('updateTime').textContent = 'Last updated: ' + new Date(data.timestamp).toLocaleString();
                
                // Update stats grid
                document.getElementById('statsGrid').innerHTML = 
                    '<div class="stat-card"><div class="stat-label">Total Hashrate</div><div class="stat-value">' + data.total_hashrate_th.toFixed(3) + ' TH/s</div></div>' +
                    '<div class="stat-card"><div class="stat-label">Total Power</div><div class="stat-value">' + data.total_power_w.toFixed(0) + ' W</div></div>' +
                    '<div class="stat-card"><div class="stat-label">Fleet Efficiency</div><div class="stat-value ' + getEfficiencyClass(data.fleet_efficiency) + '">' + data.fleet_efficiency.toFixed(1) + '%</div></div>' +
                    '<div class="stat-card"><div class="stat-label">Miners Online</div><div class="stat-value">' + data.online_count + '/' + data.total_count + '</div></div>';
                
                // Initialize UI only on first load
                if (!isInitialized) {
                    initializeUI(data);
                } else {
                    // Update existing miner data without recreating DOM elements
                    data.miners.forEach(miner => {
                        updateMinerData(miner);
                    });
                }
            }).catch(error => {
                console.error('Error fetching data:', error);
                document.getElementById('updateTime').textContent = 'Error: ' + error.message;
            });
        }
        
        updateData(); setInterval(updateData, 5000);
    </script>
</body></html>'''

def main():
    """Main function to run the enhanced BitAxe monitor"""
    
    # =================== EDIT YOUR CONFIGURATION HERE ===================
    # Replace these with your actual BitAxe miner IPs and expected hashrates
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
