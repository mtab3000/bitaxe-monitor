#!/usr/bin/env python3
"""
Enhanced BitAxe Monitor - Beautiful Design with Advanced Metrics

Professional monitoring tool with dynamic expected hashrate, J/TH efficiency, and reference lines.
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
    base_expected_hashrate_gh: float = 1100  # Base hashrate at standard frequency

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
    efficiency_j_th: float = 0  # J/TH efficiency
    temperature_c: float = 0
    frequency_mhz: float = 0
    voltage_v: float = 0
    set_voltage_v: float = 0
    uptime_s: int = 0
    fan_speed_rpm: int = 0
    chip_temp_c: float = 0

class EnhancedBitAxeMonitor:
    """Enhanced BitAxe Monitor with beautiful design and advanced metrics"""
    
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
                'expected_hashrates': deque(maxlen=self.max_data_points),
                'efficiencies': deque(maxlen=self.max_data_points),
                'j_th_efficiencies': deque(maxlen=self.max_data_points),
                'voltages': deque(maxlen=self.max_data_points),
                'temperatures': deque(maxlen=self.max_data_points)
            }
        
        # Flask routes
        self.app.route('/')(self.dashboard)
        self.app.route('/api/metrics')(self.api_metrics)
        
        # Console data collection thread
        self.running = False
        self.console_thread = None
        self.latest_metrics = {}

    def calculate_expected_hashrate(self, frequency_mhz: float, base_hashrate: float) -> float:
        """Calculate expected hashrate based on frequency scaling from base frequency"""
        base_frequency = 600.0  # Base frequency in MHz
        if frequency_mhz > 0:
            return base_hashrate * (frequency_mhz / base_frequency)
        return base_hashrate

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
                expected_hashrate_gh=miner.base_expected_hashrate_gh,
                expected_hashrate_th=miner.base_expected_hashrate_gh / 1000.0
            )
        
        try:
            # Extract basic metrics
            hashrate_gh = float(raw_data.get('hashRate', 0))
            hashrate_th = hashrate_gh / 1000.0
            power_w = float(raw_data.get('power', 0))
            temperature_c = float(raw_data.get('temp', 0))
            frequency_mhz = float(raw_data.get('frequency', 600))
            # Correct voltage fields for ASIC core voltage (try multiple possible field names)
            voltage_v = float(raw_data.get('coreVoltage', raw_data.get('vCore', raw_data.get('asicVoltage', 0))))  # Measured ASIC voltage
            set_voltage_v = float(raw_data.get('coreVoltageSet', raw_data.get('targetVoltage', raw_data.get('voltageSet', 0))))  # Set ASIC voltage
            uptime_s = int(raw_data.get('uptimeSeconds', 0))
            
            # Calculate dynamic expected hashrate based on frequency
            expected_hashrate_gh = self.calculate_expected_hashrate(frequency_mhz, miner.base_expected_hashrate_gh)
            expected_hashrate_th = expected_hashrate_gh / 1000.0
            
            # Calculate efficiency and J/TH
            efficiency_pct = (hashrate_gh / expected_hashrate_gh * 100) if expected_hashrate_gh > 0 else 0
            efficiency_j_th = (power_w / hashrate_th) if hashrate_th > 0 else 0
            
            # Store chart data
            current_time = datetime.now().strftime("%H:%M:%S")
            chart_data = self.chart_data[miner.name]
            chart_data['timestamps'].append(current_time)
            chart_data['hashrates'].append(hashrate_gh)
            chart_data['expected_hashrates'].append(expected_hashrate_gh)
            chart_data['efficiencies'].append(efficiency_pct)
            chart_data['j_th_efficiencies'].append(efficiency_j_th)
            chart_data['voltages'].append(voltage_v)
            chart_data['temperatures'].append(temperature_c)
            
            # Calculate standard deviations
            hashrates = list(chart_data['hashrates'])
            stddev_60s = statistics.stdev(hashrates[-2:]) if len(hashrates) >= 2 else 0
            stddev_300s = statistics.stdev(hashrates[-10:]) if len(hashrates) >= 10 else 0
            stddev_600s = statistics.stdev(hashrates[-20:]) if len(hashrates) >= 20 else 0
            
            return MinerMetrics(
                miner_name=miner.name,
                miner_ip=miner.ip,
                status='ONLINE',
                hashrate_gh=hashrate_gh,
                hashrate_th=hashrate_th,
                expected_hashrate_gh=expected_hashrate_gh,
                expected_hashrate_th=expected_hashrate_th,
                hashrate_efficiency_pct=efficiency_pct,
                hashrate_stddev_60s=stddev_60s,
                hashrate_stddev_300s=stddev_300s,
                hashrate_stddev_600s=stddev_600s,
                power_w=power_w,
                efficiency_j_th=efficiency_j_th,
                temperature_c=temperature_c,
                frequency_mhz=frequency_mhz,
                voltage_v=voltage_v,
                set_voltage_v=set_voltage_v,
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
                expected_hashrate_gh=miner.base_expected_hashrate_gh,
                expected_hashrate_th=miner.base_expected_hashrate_gh / 1000.0
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
        total_expected_th = sum([
            self.calculate_expected_hashrate(
                miners_data[i].get('frequency_mhz', 600) if miners_data[i]['status'] == 'ONLINE' else 600,
                miner.base_expected_hashrate_gh
            ) for i, miner in enumerate(self.miners_config)
        ]) / 1000.0
        
        fleet_efficiency = (total_hashrate_th / total_expected_th * 100) if total_expected_th > 0 else 0
        fleet_j_th = (total_power_w / total_hashrate_th) if total_hashrate_th > 0 else 0

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
            'fleet_j_th': fleet_j_th,
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
        
        # Try to enable UTF-8 encoding on Windows
        try:
            if os.name == 'nt':
                import codecs
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        except:
            pass
        
        # Check if console supports emojis
        use_emojis = True
        try:
            print("🚀", end="")
        except UnicodeEncodeError:
            use_emojis = False
        
        # Clear screen and print header
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 90)
        if use_emojis:
            print(f"🚀 Enhanced BitAxe Monitor - Console View".center(90))
            print(f"📊 {timestamp}".center(90))
        else:
            print(f"Enhanced BitAxe Monitor - Console View".center(90))
            print(f"{timestamp}".center(90))
        print("=" * 90)
        
        # Fleet summary
        if use_emojis:
            print(f"\n📈 FLEET SUMMARY")
        else:
            print(f"\nFLEET SUMMARY")
        print(f"   Total Hashrate: {metrics_data['total_hashrate_th']:.3f} TH/s")
        print(f"   Total Power:    {metrics_data['total_power_w']:.2f} W")
        print(f"   Fleet Efficiency: {metrics_data['fleet_efficiency']:.1f}%")
        print(f"   Fleet J/TH:     {metrics_data['fleet_j_th']:.2f} J/TH")
        print(f"   Miners Online:  {metrics_data['online_count']}/{metrics_data['total_count']}")
        
        # Individual miners
        if use_emojis:
            print(f"\n⚒️  MINER DETAILS")
        else:
            print(f"\nMINER DETAILS")
        print("-" * 90)
        print(f"{'Name':<18} {'Status':<8} {'Hashrate':<12} {'Efficiency':<11} {'J/TH':<8} {'Freq':<8} {'Volt':<8} {'Temp':<8}")
        print("-" * 90)
        
        for miner in metrics_data['miners']:
            if use_emojis:
                status_icon = "🟢" if miner['status'] == 'ONLINE' else "🔴"
                efficiency_color = ""
                if miner['status'] == 'ONLINE':
                    if miner['hashrate_efficiency_pct'] >= 95:
                        efficiency_color = "✅"
                    elif miner['hashrate_efficiency_pct'] >= 85:
                        efficiency_color = "⚠️ "
                    else:
                        efficiency_color = "❌"
            else:
                status_icon = "[ON]" if miner['status'] == 'ONLINE' else "[OFF]"
                efficiency_color = ""
                if miner['status'] == 'ONLINE':
                    if miner['hashrate_efficiency_pct'] >= 95:
                        efficiency_color = "[OK] "
                    elif miner['hashrate_efficiency_pct'] >= 85:
                        efficiency_color = "[WARN] "
                    else:
                        efficiency_color = "[LOW] "
            
            if miner['status'] == 'ONLINE':
                print(f"{miner['miner_name']:<18} {status_icon} {miner['status']:<6} "
                      f"{miner['hashrate_gh']:.1f} GH/s   "
                      f"{efficiency_color}{miner['hashrate_efficiency_pct']:.1f}%      "
                      f"{miner['efficiency_j_th']:.2f}   "
                      f"{miner['frequency_mhz']:.0f}MHz  "
                      f"{miner['voltage_v']:.3f}V "
                      f"{miner['temperature_c']:.1f}°C")
            else:
                print(f"{miner['miner_name']:<18} {status_icon} {miner['status']:<6} "
                      f"{'OFFLINE':<12} {'---':<11} {'---':<8} {'---':<8} {'---':<8} {'---':<8}")
        
        if use_emojis:
            print(f"\n🔄 Next update in 30 seconds... (Press Ctrl+C to stop)")
        else:
            print(f"\nNext update in 30 seconds... (Press Ctrl+C to stop)")

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
                print(f"Error in console loop: {e}")
                time.sleep(30)

    def dashboard(self):
        """Web dashboard route"""
        return render_template_string(BEAUTIFUL_HTML_TEMPLATE)

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
            print(f"Starting Enhanced BitAxe Monitor - Console Mode")
            print(f"Monitoring {len(self.miners_config)} miners:")
            for miner in self.miners_config:
                print(f"   - {miner.name} at {miner.ip} (base: {miner.base_expected_hashrate_gh} GH/s)")
            print(f"Web interface available at: http://localhost:{self.port}")
            print(f"30-second polling interval")
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
                print(f"\nMonitor stopped by user")
                self.running = False
        else:
            logging.info(f"Starting Enhanced BitAxe Monitor on port {self.port}")
            logging.info(f"Monitoring {len(self.miners_config)} miners:")
            for miner in self.miners_config:
                logging.info(f"  - {miner.name} at {miner.ip} (base: {miner.base_expected_hashrate_gh} GH/s)")
            
            try:
                self.app.run(host='0.0.0.0', port=self.port, debug=False)
            except KeyboardInterrupt:
                logging.info("Monitor stopped by user")
            except Exception as e:
                logging.error(f"Monitor error: {e}")

# Beautiful HTML Template with professional design
BEAUTIFUL_HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BitAxe Monitor - Professional Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        :root {
            --primary-blue: #1e40af;
            --primary-blue-light: #3b82f6;
            --secondary-purple: #7c3aed;
            --accent-green: #059669;
            --accent-orange: #ea580c;
            --accent-red: #dc2626;
            --dark-bg: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #64748b;
        }
        
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--dark-bg) 0%, #1e293b 100%);
            min-height: 100vh; 
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary-blue) 0%, var(--secondary-purple) 100%);
            padding: 2rem 0; 
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 30% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .header h1 { 
            font-size: 3rem; 
            font-weight: 700; 
            margin-bottom: 0.5rem;
            position: relative;
            z-index: 1;
        }
        
        .header .subtitle { 
            font-size: 1.2rem; 
            opacity: 0.9; 
            font-weight: 500;
            position: relative;
            z-index: 1;
        }
        
        .container { 
            max-width: 1800px; 
            margin: 0 auto; 
            padding: 2rem 1rem; 
        }
        
        .stats-grid {
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem; 
            margin-bottom: 3rem;
        }
        
        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 2rem; 
            border-radius: 16px;
            text-align: center; 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary-blue-light) 0%, var(--secondary-purple) 100%);
        }
        
        .stat-card:hover { 
            transform: translateY(-4px); 
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border-color: var(--primary-blue-light);
        }
        
        .stat-label { 
            display: block; 
            color: var(--text-secondary); 
            font-size: 0.95rem; 
            margin-bottom: 1rem; 
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-value { 
            font-size: 2.5rem; 
            font-weight: 700; 
            color: var(--text-primary);
            line-height: 1;
        }
        
        .miners-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(1000px, 1fr)); 
            gap: 2rem; 
        }
        
        .miner-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px; 
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); 
            transition: all 0.3s ease;
        }
        
        .miner-card:hover { 
            transform: translateY(-6px); 
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.3);
            border-color: var(--primary-blue-light);
        }
        
        .miner-header {
            background: linear-gradient(135deg, var(--primary-blue) 0%, var(--secondary-purple) 100%);
            color: white; 
            padding: 2rem; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            position: relative;
        }
        
        .miner-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
            pointer-events: none;
        }
        
        .miner-name { 
            font-size: 1.8rem; 
            font-weight: 700;
            position: relative;
            z-index: 1;
        }
        
        .status { 
            padding: 0.8rem 1.5rem; 
            border-radius: 25px; 
            font-size: 1rem; 
            font-weight: 600;
            position: relative;
            z-index: 1;
        }
        
        .status-online { 
            background: rgba(5, 150, 105, 0.2); 
            color: #10b981; 
            border: 1px solid #10b981;
        }
        
        .status-offline { 
            background: rgba(220, 38, 38, 0.2); 
            color: #ef4444; 
            border: 1px solid #ef4444;
        }
        
        .metrics-section {
            padding: 2rem; 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem; 
            border-bottom: 1px solid var(--card-border);
            background: rgba(15, 23, 42, 0.3);
        }
        
        .metric { 
            text-align: center;
            padding: 1rem;
            background: var(--card-bg);
            border-radius: 12px;
            border: 1px solid var(--card-border);
            transition: all 0.3s ease;
        }
        
        .metric:hover {
            border-color: var(--primary-blue-light);
            transform: translateY(-2px);
        }
        
        .metric-label { 
            display: block; 
            color: var(--text-secondary); 
            font-size: 0.85rem; 
            margin-bottom: 0.8rem; 
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-value { 
            font-size: 1.5rem; 
            font-weight: 700; 
            color: var(--text-primary);
        }
        
        .efficiency-excellent { color: var(--accent-green); }
        .efficiency-good { color: var(--accent-orange); }
        .efficiency-poor { color: var(--accent-red); }
        
        .charts-section { 
            padding: 2rem; 
            background: rgba(15, 23, 42, 0.2);
        }
        
        .charts-grid { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 2rem; 
        }
        
        .chart-container { 
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px; 
            padding: 1.5rem; 
            height: 320px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .chart-container:hover {
            border-color: var(--primary-blue-light);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }
        
        .chart-title { 
            font-size: 1.2rem; 
            color: var(--text-primary); 
            margin-bottom: 1rem; 
            text-align: center; 
            font-weight: 600;
        }
        
        .update-time { 
            text-align: center; 
            color: var(--text-muted); 
            margin-top: 3rem; 
            font-size: 1rem; 
            font-weight: 500;
            padding: 1rem;
            background: var(--card-bg);
            border-radius: 8px;
            border: 1px solid var(--card-border);
        }
        
        @media (max-width: 1200px) {
            .charts-grid { grid-template-columns: 1fr; }
            .miners-grid { grid-template-columns: 1fr; }
            .header h1 { font-size: 2.5rem; }
        }
        
        @media (max-width: 768px) {
            .container { padding: 1rem; }
            .metrics-section { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; }
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--dark-bg);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--primary-blue);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-blue-light);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>BitAxe Monitor</h1>
        <div class="subtitle">Professional Mining Dashboard • Real-time Analytics • 30s Refresh</div>
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
                    title: '⚡ Hashrate Performance', 
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    dataKey: 'hashrates',
                    referenceLine: true,
                    referenceDataKey: 'expected_hashrates'
                },
                { 
                    id: `efficiency-chart-${minerIdSafe}`, 
                    title: '📊 Mining Efficiency', 
                    borderColor: '#059669',
                    backgroundColor: 'rgba(5, 150, 105, 0.1)',
                    dataKey: 'efficiencies',
                    referenceLine: true,
                    referenceValue: 100
                },
                { 
                    id: `jth-chart-${minerIdSafe}`, 
                    title: '🔥 J/TH Efficiency', 
                    borderColor: '#ea580c',
                    backgroundColor: 'rgba(234, 88, 12, 0.1)',
                    dataKey: 'j_th_efficiencies'
                },
                { 
                    id: `voltage-chart-${minerIdSafe}`, 
                    title: '⚡ Voltage & Temperature', 
                    borderColor: '#7c3aed',
                    backgroundColor: 'rgba(124, 58, 237, 0.1)',
                    dataKey: 'voltages',
                    referenceLine: true,
                    referenceValue: 1.000
                }
            ];

            chartConfigs.forEach(config => {
                const ctx = document.getElementById(config.id);
                if (ctx) {
                    const datasets = [{
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
                    }];

                    // Add reference line dataset if needed
                    if (config.referenceLine) {
                        datasets.push({
                            label: 'Reference',
                            data: [],
                            borderColor: '#64748b',
                            backgroundColor: 'transparent',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            pointRadius: 0,
                            fill: false,
                            tension: 0
                        });
                    }

                    charts[config.id] = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: datasets
                        },
                        options: {
                            responsive: true, 
                            maintainAspectRatio: false,
                            plugins: { 
                                legend: { 
                                    display: false 
                                },
                                tooltip: {
                                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                    titleColor: '#f8fafc',
                                    bodyColor: '#cbd5e1',
                                    borderColor: config.borderColor,
                                    borderWidth: 1,
                                    cornerRadius: 8
                                }
                            },
                            scales: { 
                                x: {
                                    grid: { 
                                        color: 'rgba(100, 116, 139, 0.2)',
                                        drawBorder: false
                                    },
                                    ticks: { 
                                        color: '#64748b',
                                        font: { size: 11 }
                                    }
                                },
                                y: { 
                                    beginAtZero: false,
                                    grid: { 
                                        color: 'rgba(100, 116, 139, 0.2)',
                                        drawBorder: false
                                    },
                                    ticks: { 
                                        color: '#64748b',
                                        font: { size: 11 }
                                    }
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
                { id: `hashrate-chart-${minerIdSafe}`, dataKey: 'hashrates', referenceDataKey: 'expected_hashrates' },
                { id: `efficiency-chart-${minerIdSafe}`, dataKey: 'efficiencies', referenceValue: 100 },
                { id: `jth-chart-${minerIdSafe}`, dataKey: 'j_th_efficiencies' },
                { id: `voltage-chart-${minerIdSafe}`, dataKey: 'voltages', referenceValue: 1.000 }
            ];

            chartConfigs.forEach(config => {
                const chart = charts[config.id];
                if (chart && minerChartData[config.dataKey]) {
                    chart.data.labels = Array.from(minerChartData.timestamps);
                    chart.data.datasets[0].data = Array.from(minerChartData[config.dataKey]);
                    
                    // Update reference line if exists
                    if (chart.data.datasets.length > 1) {
                        if (config.referenceDataKey && minerChartData[config.referenceDataKey]) {
                            chart.data.datasets[1].data = Array.from(minerChartData[config.referenceDataKey]);
                        } else if (config.referenceValue !== undefined) {
                            const referenceArray = new Array(minerChartData.timestamps.length).fill(config.referenceValue);
                            chart.data.datasets[1].data = referenceArray;
                        }
                    }
                    
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
                                    <div class="chart-title">⚡ Hashrate Performance</div>
                                    <canvas id="hashrate-chart-${minerIdSafe}"></canvas>
                                </div>
                                <div class="chart-container">
                                    <div class="chart-title">📊 Mining Efficiency</div>
                                    <canvas id="efficiency-chart-${minerIdSafe}"></canvas>
                                </div>
                                <div class="chart-container">
                                    <div class="chart-title">🔥 J/TH Efficiency</div>
                                    <canvas id="jth-chart-${minerIdSafe}"></canvas>
                                </div>
                                <div class="chart-container">
                                    <div class="chart-title">⚡ Voltage & Temperature</div>
                                    <canvas id="voltage-chart-${minerIdSafe}"></canvas>
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
                            <div class="metric">
                                <span class="metric-label">Status</span>
                                <span class="metric-value">OFFLINE</span>
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
                        <span class="metric-label">Hashrate</span>
                        <span class="metric-value">${miner.hashrate_gh.toFixed(1)} GH/s</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Expected</span>
                        <span class="metric-value">${miner.expected_hashrate_gh.toFixed(1)} GH/s</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Efficiency</span>
                        <span class="metric-value ${getEfficiencyClass(miner.hashrate_efficiency_pct)}">${miner.hashrate_efficiency_pct.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">J/TH</span>
                        <span class="metric-value">${miner.efficiency_j_th.toFixed(2)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Power</span>
                        <span class="metric-value">${miner.power_w.toFixed(2)}W</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Frequency</span>
                        <span class="metric-value">${miner.frequency_mhz.toFixed(0)} MHz</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Set Voltage</span>
                        <span class="metric-value">${miner.set_voltage_v.toFixed(3)}V</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Measured Voltage</span>
                        <span class="metric-value">${miner.voltage_v.toFixed(3)}V</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Temperature</span>
                        <span class="metric-value">${miner.temperature_c.toFixed(2)}°C</span>
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
                        `🔄 Last updated: ${new Date().toLocaleTimeString()} • Next update in 30s`;
                    
                    // Update fleet stats
                    document.getElementById('statsGrid').innerHTML = `
                        <div class="stat-card">
                            <div class="stat-label">Total Hashrate</div>
                            <div class="stat-value">${data.total_hashrate_th.toFixed(3)} TH/s</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Power</div>
                            <div class="stat-value">${data.total_power_w.toFixed(2)} W</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Fleet Efficiency</div>
                            <div class="stat-value ${getEfficiencyClass(data.fleet_efficiency)}">${data.fleet_efficiency.toFixed(1)}%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Fleet J/TH</div>
                            <div class="stat-value">${data.fleet_j_th.toFixed(2)}</div>
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
                    document.getElementById('updateTime').textContent = '❌ Error: ' + error.message;
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
        {'name': 'BitAxe-Gamma-1', 'ip': '192.168.1.45', 'base_expected_hashrate_gh': 1200},
        {'name': 'BitAxe-Gamma-2', 'ip': '192.168.1.46', 'base_expected_hashrate_gh': 1150},
        {'name': 'BitAxe-Gamma-3', 'ip': '192.168.1.47', 'base_expected_hashrate_gh': 1100}
    ]
    # =====================================================================
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create and run the enhanced monitor
    monitor = EnhancedBitAxeMonitor(miners_config, port=args.port, console_mode=args.console)
    monitor.run()

if __name__ == '__main__':
    main()
