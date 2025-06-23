#!/usr/bin/env python3
"""
Enhanced BitAxe Monitor - Complete Implementation with Console View

Working monitor with advanced charts, variance tracking, statistical analysis, and console output.
"""

import sys
import os
import time
import requests
import statistics
import threading
import argparse
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

class EnhancedBitAxeMonitor:
    """Enhanced BitAxe Monitor with console and web interface"""
    
    def __init__(self, miners_config_raw: List[Dict], port: int = 8080, console_mode: bool = False):
        self.miners_config = [MinerConfig(**config) for config in miners_config_raw]
        self.port = port
        self.console_mode = console_mode
        self.app = Flask(__name__)
        
        # Chart data storage with 60-minute capacity (120 data points at 30s intervals)
        self.chart_data = {}
        self.max_data_points = 120  # 60 minutes at 30-second intervals
        
        for miner in self.miners_config:
            self.chart_data[miner.name] = {
                'timestamps': deque(maxlen=self.max_data_points),
                'hashrates': deque(maxlen=self.max_data_points),
                'variances': deque(maxlen=self.max_data_points),
                'efficiencies': deque(maxlen=self.max_data_points),
                'std_devs': deque(maxlen=self.max_data_points),
                'power': deque(maxlen=self.max_data_points),
                'temperature': deque(maxlen=self.max_data_points)
            }
        
        # Flask routes
        self.app.route('/')(self.dashboard)
        self.app.route('/api/metrics')(self.api_metrics)
        
        # Console data collection thread
        self.running = False
        self.console_thread = None
        self.latest_metrics = {}

    def fetch_miner_data(self, miner: MinerConfig) -> Optional[Dict]:
        """Fetch data from a single BitAxe miner"""
        try:
            response = requests.get(f'http://{miner.ip}/api/system/info', timeout=5)
            response.raise_for_status()
            data = response.json()
            if self.console_mode:
                print(f"[DEBUG] Fetched data from {miner.name} ({miner.ip}): {data}")
            return data
        except requests.exceptions.RequestException as e:
            if self.console_mode:
                print(f"[WARNING] Failed to fetch data from {miner.name} ({miner.ip}): {e}")
            logging.warning(f"Failed to fetch data from {miner.name} ({miner.ip}): {e}")
            return None    

    def parse_miner_metrics(self, miner: MinerConfig, raw_data: Dict) -> MinerMetrics:
        """Parse raw API data into structured metrics"""
        if not raw_data:
            return MinerMetrics(
                miner_name=miner.name,
                miner_ip=miner.ip,
                status='OFFLINE',
                expected_hashrate_gh=miner.expected_hashrate_gh,
                expected_hashrate_th=miner.expected_hashrate_gh / 1000.0
            )
        
        try:
            # Extract basic metrics
            hashrate_gh = float(raw_data.get('hashRate', 0))
            hashrate_th = hashrate_gh / 1000.0
            power_w = float(raw_data.get('power', 0))
            temperature_c = float(raw_data.get('temp', 0))
            uptime_s = int(raw_data.get('uptimeSeconds', 0))
            
            # Calculate efficiency
            efficiency_pct = (hashrate_gh / miner.expected_hashrate_gh * 100) if miner.expected_hashrate_gh > 0 else 0
            
            # Store chart data
            current_time = datetime.now().strftime("%H:%M:%S")
            chart_data = self.chart_data[miner.name]
            chart_data['timestamps'].append(current_time)
            chart_data['hashrates'].append(hashrate_gh)
            chart_data['variances'].append(hashrate_gh - miner.expected_hashrate_gh)
            chart_data['efficiencies'].append(efficiency_pct)
            chart_data['power'].append(power_w)
            chart_data['temperature'].append(temperature_c)
            
            # Calculate standard deviations
            hashrates = list(chart_data['hashrates'])
            stddev_60s = statistics.stdev(hashrates[-2:]) if len(hashrates) >= 2 else 0
            stddev_300s = statistics.stdev(hashrates[-10:]) if len(hashrates) >= 10 else 0
            stddev_600s = statistics.stdev(hashrates[-20:]) if len(hashrates) >= 20 else 0
            chart_data['std_devs'].append(stddev_60s)
            
            return MinerMetrics(
                miner_name=miner.name,
                miner_ip=miner.ip,
                status='ONLINE',
                hashrate_gh=hashrate_gh,
                hashrate_th=hashrate_th,
                expected_hashrate_gh=miner.expected_hashrate_gh,
                expected_hashrate_th=miner.expected_hashrate_gh / 1000.0,
                hashrate_efficiency_pct=efficiency_pct,
                hashrate_stddev_60s=stddev_60s,
                hashrate_stddev_300s=stddev_300s,
                hashrate_stddev_600s=stddev_600s,
                power_w=power_w,
                temperature_c=temperature_c,
                frequency_mhz=float(raw_data.get('frequency', 0)),
                voltage_v=float(raw_data.get('voltage', 0)),
                uptime_s=uptime_s,
                fan_speed_rpm=int(raw_data.get('fanSpeed', 0)),
                chip_temp_c=float(raw_data.get('chipTemp', temperature_c))
            )
            
        except (KeyError, ValueError, TypeError) as e:
            logging.warning(f"Error parsing data for {miner.name}: {e}")
            return MinerMetrics(
                miner_name=miner.name,
                miner_ip=miner.ip,
                status='PARSE_ERROR',
                expected_hashrate_gh=miner.expected_hashrate_gh,
                expected_hashrate_th=miner.expected_hashrate_gh / 1000.0
            )

    def collect_all_metrics(self) -> Dict:
        """Collect metrics from all miners"""
        miners_data = []
        total_hashrate_th = 0
        total_power_w = 0
        online_count = 0
        
        for miner in self.miners_config:
            raw_data = self.fetch_miner_data(miner)
            metrics = self.parse_miner_metrics(miner, raw_data if raw_data is not None else {})
            miners_data.append(metrics.__dict__)
            
            if metrics.status == 'ONLINE':
                total_hashrate_th += metrics.hashrate_th
                total_power_w += metrics.power_w
                online_count += 1
        
        # Calculate fleet efficiency
        total_expected_th = sum(miner.expected_hashrate_gh for miner in self.miners_config) / 1000.0
        fleet_efficiency = (total_hashrate_th / total_expected_th * 100) if total_expected_th > 0 else 0

        # Convert all deques in chart_data to lists for JSON serialization
        serializable_chart_data = {}
        for miner_name, miner_chart in self.chart_data.items():
            serializable_chart_data[miner_name] = {
                key: list(value) for key, value in miner_chart.items()
            }

        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'total_hashrate_th': total_hashrate_th,
            'total_power_w': total_power_w,
            'fleet_efficiency': fleet_efficiency,
            'online_count': online_count,
            'total_count': len(self.miners_config),
            'miners': miners_data,
            'chart_data': serializable_chart_data
        }
        
        # Store for console access
        self.latest_metrics = metrics_data
        return metrics_data

    def print_console_summary(self, metrics_data: Dict):
        """Print formatted console summary"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Clear screen and print header
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 80)
        print(f"🚀 Enhanced BitAxe Monitor - Console View".center(80))
        print(f"📊 {timestamp}".center(80))
        print("=" * 80)
        
        # Fleet summary
        print(f"\n📈 FLEET SUMMARY")
        print(f"   Total Hashrate: {metrics_data['total_hashrate_th']:.3f} TH/s")
        print(f"   Total Power:    {metrics_data['total_power_w']:.1f} W")
        print(f"   Fleet Efficiency: {metrics_data['fleet_efficiency']:.1f}%")
        print(f"   Miners Online:  {metrics_data['online_count']}/{metrics_data['total_count']}")
        
        # Individual miners
        print(f"\n⚒️  MINER DETAILS")
        print("-" * 80)
        print(f"{'Name':<20} {'Status':<8} {'Hashrate':<12} {'Efficiency':<12} {'Power':<8} {'Temp':<8}")
        print("-" * 80)
        
        for miner in metrics_data['miners']:
            status_icon = "🟢" if miner['status'] == 'ONLINE' else "🔴"
            efficiency_color = ""
            if miner['status'] == 'ONLINE':
                if miner['hashrate_efficiency_pct'] >= 95:
                    efficiency_color = "✅"
                elif miner['hashrate_efficiency_pct'] >= 85:
                    efficiency_color = "⚠️ "
                else:
                    efficiency_color = "❌"
            
            print(f"{miner['miner_name']:<20} {status_icon} {miner['status']:<6} "
                  f"{miner['hashrate_gh']:.1f} GH/s    "
                  f"{efficiency_color}{miner['hashrate_efficiency_pct']:.1f}%       "
                  f"{miner['power_w']:.1f} W   "
                  f"{miner['temperature_c']:.1f}°C")
        
        print(f"\n🔄 Next update in 30 seconds... (Press Ctrl+C to stop)")

    def console_data_loop(self):
        """Console data collection loop"""
        while self.running:
            try:
                metrics_data = self.collect_all_metrics()
                if self.console_mode:
                    self.print_console_summary(metrics_data)
                time.sleep(30)  # 30-second polling interval
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"❌ Error in console loop: {e}")
                time.sleep(30)

    def dashboard(self):
        """Web dashboard route"""
        return render_template_string(ENHANCED_HTML_TEMPLATE)

    def api_metrics(self):
        """API endpoint for metrics data"""
        if self.console_mode and self.latest_metrics:
            return jsonify(self.latest_metrics)
        else:
            return jsonify(self.collect_all_metrics())

    def run(self):
        """Run the enhanced monitor"""
        self.running = True
        
        if self.console_mode:
            print(f"🚀 Starting Enhanced BitAxe Monitor - Console Mode")
            print(f"📊 Monitoring {len(self.miners_config)} miners:")
            for miner in self.miners_config:
                print(f"   - {miner.name} at {miner.ip} (expected: {miner.expected_hashrate_gh} GH/s)")
            print(f"🌐 Web interface available at: http://localhost:{self.port}")
            print(f"⏱️  30-second polling interval")
            print("\n" + "=" * 80)
            
            # Start console data collection in separate thread
            self.console_thread = threading.Thread(target=self.console_data_loop, daemon=True)
            self.console_thread.start()
            
            # Start Flask in background
            flask_thread = threading.Thread(
                target=lambda: self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False),
                daemon=True
            )
            flask_thread.start()
            
            try:
                # Keep main thread alive for console updates
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n🛑 Monitor stopped by user")
                self.running = False
        else:
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

# Enhanced HTML Template with beautiful charts
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
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh; color: #333;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95); padding: 2rem 0; text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); margin-bottom: 2rem;
            backdrop-filter: blur(10px);
        }
        
        .header h1 { 
            color: #2d3748; font-size: 2.8rem; font-weight: 600; margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .header .subtitle { color: #4a5568; font-size: 1.3rem; font-weight: 500; }
        .container { max-width: 1600px; margin: 0 auto; padding: 0 1rem; }
        
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem; margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95); padding: 2rem; border-radius: 16px;
            text-align: center; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .stat-card:hover { 
            transform: translateY(-5px); 
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        }
        .stat-label { display: block; color: #718096; font-size: 1rem; margin-bottom: 0.8rem; font-weight: 500; }
        .stat-value { font-size: 2.2rem; font-weight: 700; color: #2d3748; }
        
        .miners-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(900px, 1fr)); gap: 2rem; }
        
        .miner-card {
            background: rgba(255, 255, 255, 0.98); border-radius: 20px; overflow: hidden;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15); transition: all 0.3s ease;
            backdrop-filter: blur(15px);
        }
        
        .miner-card:hover { transform: translateY(-8px); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2); }
        
        .miner-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 2rem; display: flex; justify-content: space-between; align-items: center;
        }
        
        .miner-name { font-size: 1.6rem; font-weight: 700; }
        .status { padding: 0.6rem 1.5rem; border-radius: 25px; font-size: 1rem; font-weight: 600; }
        .status-online { background: rgba(72, 187, 120, 0.2); color: #2f855a; }
        .status-offline { background: rgba(245, 101, 101, 0.2); color: #c53030; }
        
        .metrics-section {
            padding: 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1.5rem; border-bottom: 1px solid #e2e8f0;
        }
        
        .metric { text-align: center; }
        .metric-label { display: block; color: #718096; font-size: 0.9rem; margin-bottom: 0.6rem; font-weight: 500; }
        .metric-value { font-size: 1.5rem; font-weight: 700; color: #2d3748; }
        
        .efficiency-excellent { color: #38a169; }
        .efficiency-good { color: #d69e2e; }
        .efficiency-poor { color: #e53e3e; }
        
        .charts-section { padding: 2rem; }
        .charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
        .chart-container { 
            background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%); 
            border-radius: 16px; padding: 1.5rem; height: 300px;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.06);
        }
        .chart-title { 
            font-size: 1.1rem; color: #4a5568; margin-bottom: 1rem; text-align: center; 
            font-weight: 600;
        }
        
        .update-time { 
            text-align: center; color: rgba(255, 255, 255, 0.8); margin-top: 2rem; 
            font-size: 1rem; font-weight: 500;
        }
        
        @media (max-width: 1200px) {
            .charts-grid { grid-template-columns: 1fr; }
            .miners-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Enhanced BitAxe Monitor</h1>
        <div class="subtitle">Real-time Mining Performance • 60-Minute Analytics • 30s Refresh</div>
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
                { 
                    id: `hashrate-chart-${minerIdSafe}`, 
                    title: 'Hashrate (GH/s)', 
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    dataKey: 'hashrates' 
                },
                { 
                    id: `variance-chart-${minerIdSafe}`, 
                    title: 'Directional Variance', 
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    dataKey: 'variances' 
                },
                { 
                    id: `efficiency-chart-${minerIdSafe}`, 
                    title: 'Efficiency (%)', 
                    borderColor: 'rgb(16, 185, 129)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    dataKey: 'efficiencies' 
                },
                { 
                    id: `power-chart-${minerIdSafe}`, 
                    title: 'Power & Temperature', 
                    borderColor: 'rgb(245, 158, 11)',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    dataKey: 'power' 
                }
            ];

            chartConfigs.forEach(config => {
                const ctx = document.getElementById(config.id);
                if (ctx) {
                    charts[config.id] = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: config.title, 
                                data: [], 
                                borderColor: config.borderColor,
                                backgroundColor: config.backgroundColor, 
                                tension: 0.4, 
                                fill: true,
                                borderWidth: 3,
                                pointRadius: 4,
                                pointBackgroundColor: config.borderColor,
                                pointBorderColor: '#ffffff',
                                pointBorderWidth: 2
                            }]
                        },
                        options: {
                            responsive: true, 
                            maintainAspectRatio: false,
                            plugins: { 
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                    titleColor: '#fff',
                                    bodyColor: '#fff',
                                    borderColor: config.borderColor,
                                    borderWidth: 1
                                }
                            },
                            scales: { 
                                x: {
                                    grid: { color: 'rgba(0, 0, 0, 0.1)' },
                                    ticks: { color: '#6b7280' }
                                },
                                y: { 
                                    beginAtZero: config.dataKey === 'variances' ? false : true,
                                    grid: { color: 'rgba(0, 0, 0, 0.1)' },
                                    ticks: { color: '#6b7280' }
                                }
                            },
                            elements: {
                                point: {
                                    hoverRadius: 8
                                }
                            }
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
                { id: `power-chart-${minerIdSafe}`, dataKey: 'power' }
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
                                    <div class="chart-title">📈 Hashrate (GH/s)</div>
                                    <canvas id="hashrate-chart-${minerIdSafe}"></canvas>
                                </div>
                                <div class="chart-container">
                                    <div class="chart-title">📊 Directional Variance</div>
                                    <canvas id="variance-chart-${minerIdSafe}"></canvas>
                                </div>
                                <div class="chart-container">
                                    <div class="chart-title">⚡ Efficiency (%)</div>
                                    <canvas id="efficiency-chart-${minerIdSafe}"></canvas>
                                </div>
                                <div class="chart-container">
                                    <div class="chart-title">🔥 Power & Temperature</div>
                                    <canvas id="power-chart-${minerIdSafe}"></canvas>
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
        }
        
        function updateMinerData(miner, data) {
            const minerIdSafe = miner.miner_name.replace(/[^a-zA-Z0-9]/g, '');
            // Update status
            const statusElem = document.getElementById(`status-${minerIdSafe}`);
            if (statusElem) {
                statusElem.textContent = miner.status;
                statusElem.className = 'status ' + (miner.status === 'ONLINE' ? 'status-online' : 'status-offline');
            }
            // Update metrics
            const metricsElem = document.getElementById(`metrics-${minerIdSafe}`);
            if (metricsElem && miner.status === 'ONLINE') {
                metricsElem.innerHTML = `
                    <div class="metric">
                        <span class="metric-label">IP Address</span>
                        <span class="metric-value">${miner.miner_ip}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Hashrate</span>
                        <span class="metric-value">${miner.hashrate_gh.toFixed(1)} GH/s</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Efficiency</span>
                        <span class="metric-value ${getEfficiencyClass(miner.hashrate_efficiency_pct)}">${miner.hashrate_efficiency_pct.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Power</span>
                        <span class="metric-value">${miner.power_w} W</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Temp</span>
                        <span class="metric-value">${miner.temperature_c}°C</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Uptime</span>
                        <span class="metric-value">${Math.floor(miner.uptime_s/3600)}h ${(Math.floor(miner.uptime_s/60)%60)}m</span>
                    </div>
                `;
            }
            // Update charts
            updateCharts(miner.miner_name, data);
        }

        function updateData() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('updateTime').textContent = 
                        `Last updated: ${new Date().toLocaleTimeString()} • Next update in 30s`;
                    
                    // Update fleet stats
                    document.getElementById('statsGrid').innerHTML = `
                        <div class="stat-card">
                            <div class="stat-label">Total Hashrate</div>
                            <div class="stat-value">${data.total_hashrate_th.toFixed(3)} TH/s</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Power</div>
                            <div class="stat-value">${data.total_power_w.toFixed(1)} W</div>
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
        setInterval(updateData, 30000); // 30-second intervals
    </script>
</body>
</html>'''

def main():
    """Main function to run the enhanced BitAxe monitor"""
    
    parser = argparse.ArgumentParser(description='Enhanced BitAxe Monitor')
    parser.add_argument('--console', '-c', action='store_true', 
                       help='Run in console mode with terminal output')
    parser.add_argument('--port', '-p', type=int, default=8080,
                       help='Web server port (default: 8080)')
    
    args = parser.parse_args()
    
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
    monitor = EnhancedBitAxeMonitor(miners_config, port=args.port, console_mode=args.console)
    monitor.run()

if __name__ == '__main__':
    main()
