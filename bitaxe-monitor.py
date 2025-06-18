#!/usr/bin/env python3
"""
Multi-Bitaxe Gamma Miner KPI Monitor
Polls multiple miners every 60 seconds for performance metrics
"""

import requests
import time
import json
from datetime import datetime
import csv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

class MultiBitaxeMonitor:
    def __init__(self, miners_config):
        """
        Initialize the Multi-Bitaxe monitor
        
        Args:
            miners_config (list): List of dicts with 'name', 'ip', and optional 'port'
            Example: [
                {'name': 'Gamma-1', 'ip': '192.168.1.100'},
                {'name': 'Gamma-2', 'ip': '192.168.1.101', 'port': 80},
                {'name': 'Gamma-3', 'ip': '192.168.1.102'}
            ]
        """
        self.miners = miners_config
        self.csv_filename = f"multi_bitaxe_kpis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.setup_csv()
    
    def setup_csv(self):
        """Setup CSV file with headers"""
        headers = [
            'timestamp', 'miner_name', 'miner_ip', 'hashrate_gh', 'hashrate_th', 'power_w', 'efficiency_jth', 
            'temperature_c', 'vr_temperature_c', 'fan_speed_rpm', 'voltage_v', 'input_voltage_v', 'frequency_mhz',
            'best_diff', 'session_diff', 'accepted_shares', 'rejected_shares',
            'uptime_s', 'wifi_rssi', 'pool_url', 'worker_name', 'asic_model',
            'board_version', 'firmware_version', 'status'
        ]
        
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def get_bitaxe_data(self, miner):
        """Get all data from /api/system/info for a single miner"""
        try:
            port = miner.get('port', 80)
            url = f"http://{miner['ip']}:{port}/api/system/info"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching data from {miner['name']} ({miner['ip']}): {e}")
            return None
    
    def collect_miner_kpis(self, miner):
        """Collect all KPIs from a single miner"""
        timestamp = datetime.now().isoformat()
        
        # Get all data from single endpoint
        data = self.get_bitaxe_data(miner)
        
        if not data:
            # Return error record
            return {
                'timestamp': timestamp,
                'miner_name': miner['name'],
                'miner_ip': miner['ip'],
                'status': 'OFFLINE',
                'hashrate_gh': 0,
                'hashrate_th': 0,
                'power_w': 0,
                'efficiency_jth': 0,
                'temperature_c': 0,
                'vr_temperature_c': 0,
                'fan_speed_rpm': 0,
                'voltage_v': 0,
                'input_voltage_v': 0,
                'frequency_mhz': 0,
                'best_diff': 0,
                'session_diff': 0,
                'accepted_shares': 0,
                'rejected_shares': 0,
                'uptime_s': 0,
                'wifi_rssi': 0,
                'pool_url': '',
                'worker_name': '',
                'asic_model': '',
                'board_version': '',
                'firmware_version': ''
            }
        
        # Extract KPIs from the response
        # hashRate from API is already in GH/s, convert to TH/s
        hashrate_gh = data.get('hashRate', 0)  # Already in GH/s
        hashrate_th = hashrate_gh / 1000  # Convert GH/s to TH/s
        
        kpis = {
            'timestamp': timestamp,
            'miner_name': miner['name'],
            'miner_ip': miner['ip'],
            'status': 'ONLINE',
            'hashrate_gh': hashrate_gh,
            'hashrate_th': hashrate_th,
            'power_w': data.get('power', 0),
            'efficiency_jth': 0,  # Will calculate below (J/TH)
            'temperature_c': data.get('temp', 0),
            'vr_temperature_c': data.get('vrTemp', 0),
            'fan_speed_rpm': data.get('fanrpm', 0),
            'voltage_v': data.get('coreVoltageActual', 0) / 1000,  # Convert mV to V (core voltage)
            'input_voltage_v': data.get('voltage', 0) / 1000,  # Convert mV to V (input voltage)
            'frequency_mhz': data.get('frequency', 0),
            'best_diff': data.get('bestNonceDiff', 0),
            'session_diff': data.get('bestSessionNonceDiff', 0),
            'accepted_shares': data.get('sharesAccepted', 0),
            'rejected_shares': data.get('sharesRejected', 0),
            'uptime_s': data.get('uptimeSeconds', 0),
            'wifi_rssi': data.get('wifiRSSI', 0),
            'pool_url': data.get('stratumURL', ''),
            'worker_name': data.get('stratumUser', ''),
            'asic_model': data.get('ASICModel', ''),
            'board_version': data.get('boardVersion', ''),
            'firmware_version': data.get('version', '')
        }
        
        # Calculate efficiency (J/TH)
        if hashrate_th > 0:
            kpis['efficiency_jth'] = kpis['power_w'] / hashrate_th
        
        return kpis
    
    def collect_all_kpis(self):
        """Collect KPIs from all miners concurrently"""
        all_kpis = []
        
        # Use ThreadPoolExecutor to query all miners simultaneously
        with ThreadPoolExecutor(max_workers=len(self.miners)) as executor:
            # Submit all tasks
            future_to_miner = {
                executor.submit(self.collect_miner_kpis, miner): miner 
                for miner in self.miners
            }
            
            # Collect results
            for future in as_completed(future_to_miner):
                miner = future_to_miner[future]
                try:
                    kpis = future.result()
                    all_kpis.append(kpis)
                except Exception as e:
                    print(f"❌ Exception collecting data from {miner['name']}: {e}")
                    # Add error record
                    all_kpis.append({
                        'timestamp': datetime.now().isoformat(),
                        'miner_name': miner['name'],
                        'miner_ip': miner['ip'],
                        'status': 'ERROR',
                        'hashrate_gh': 0, 'hashrate_th': 0, 'power_w': 0,
                        'efficiency_jth': 0, 'temperature_c': 0, 'vr_temperature_c': 0, 'fan_speed_rpm': 0,
                        'voltage_v': 0, 'input_voltage_v': 0, 'frequency_mhz': 0, 'best_diff': 0,
                        'session_diff': 0, 'accepted_shares': 0, 'rejected_shares': 0,
                        'uptime_s': 0, 'wifi_rssi': 0, 'pool_url': '', 'worker_name': '',
                        'asic_model': '', 'board_version': '', 'firmware_version': ''
                    })
        
        return sorted(all_kpis, key=lambda x: x['miner_name'])
    
    def log_to_csv(self, all_kpis):
        """Log all miners' KPIs to CSV file"""
        if not all_kpis:
            return
        
        with open(self.csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            for kpis in all_kpis:
                row = [
                    kpis['timestamp'], kpis['miner_name'], kpis['miner_ip'],
                    kpis['hashrate_gh'], kpis['hashrate_th'], kpis['power_w'],
                    kpis['efficiency_jth'], kpis['temperature_c'], kpis['vr_temperature_c'], 
                    kpis['fan_speed_rpm'], kpis['voltage_v'], kpis['input_voltage_v'], 
                    kpis['frequency_mhz'], kpis['best_diff'], kpis['session_diff'], 
                    kpis['accepted_shares'], kpis['rejected_shares'], kpis['uptime_s'], 
                    kpis['wifi_rssi'], kpis['pool_url'], kpis['worker_name'], 
                    kpis['asic_model'], kpis['board_version'], kpis['firmware_version'], 
                    kpis['status']
                ]
                writer.writerow(row)
    
    def display_summary(self, all_kpis):
        """Display summary of all miners"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n🔥 Multi-Bitaxe Summary - {timestamp}")
        print("=" * 125)
        print(f"{'Miner':<12} {'Hashrate':>12} {'Power':>8} {'Efficiency':>15} {'ASIC':>8} {'VR':>8} {'Core':>8} {'Input':>10} {'Freq':>8} {'Fan':>10}")
        print("-" * 125)
        
        total_hashrate_th = 0
        total_power = 0
        online_count = 0
        
        for kpis in all_kpis:
            status_icon = "🟢" if kpis['status'] == 'ONLINE' else "🔴"
            
            if kpis['status'] == 'ONLINE':
                print(f"{status_icon} {kpis['miner_name']:<10} {kpis['hashrate_th']:>8.3f} TH/s {kpis['power_w']:>6.1f}W {'**' + str(kpis['efficiency_jth'])[:5] + ' J/TH**':>15} {kpis['temperature_c']:>6.1f}°C {kpis['vr_temperature_c']:>6.1f}°C {kpis['voltage_v']:>6.3f}V {kpis['input_voltage_v']:>8.2f}V {kpis['frequency_mhz']:>6}MHz {kpis['fan_speed_rpm']:>8}RPM")
                total_hashrate_th += kpis['hashrate_th']
                total_power += kpis['power_w']
                online_count += 1
            else:
                print(f"{status_icon} {kpis['miner_name']:<10} {'OFFLINE':>70}")
        
        print("-" * 125)
        if online_count > 0:
            avg_efficiency = total_power / total_hashrate_th if total_hashrate_th > 0 else 0
            print(f"📊 {'TOTALS':<10} {total_hashrate_th:>8.3f} TH/s {total_power:>6.1f}W {'**' + str(avg_efficiency)[:5] + ' J/TH**':>15} {online_count}/{len(self.miners)} miners online")
        else:
            print(f"❌ All miners offline ({0}/{len(self.miners)} online)")
        print()
    
    def display_detailed_kpis(self, all_kpis):
        """Display detailed KPIs for each miner"""
        for i, kpis in enumerate(all_kpis):
            if kpis['status'] != 'ONLINE':
                continue
                
            print(f"\n🔥 {kpis['miner_name']} ({kpis['miner_ip']}) - {kpis['timestamp'][:19]}")
            print("=" * 50)
            print(f"⚡ Hashrate:      {kpis['hashrate_gh']:.2f} GH/s ({kpis['hashrate_th']:.3f} TH/s)")
            print(f"🔌 Power:         {kpis['power_w']:.1f} W")
            print(f"⚙️  Efficiency:    **{kpis['efficiency_jth']:.2f} J/TH**")
            print(f"🌡️  Temperature:   {kpis['temperature_c']:.1f}°C (ASIC) / {kpis['vr_temperature_c']:.1f}°C (VR)")
            print(f"💨 Fan Speed:     {kpis['fan_speed_rpm']} RPM")
            print(f"⚡ Voltage:       {kpis['voltage_v']:.3f} V (Core) / {kpis['input_voltage_v']:.2f} V (Input)")
            print(f"📡 Frequency:     {kpis['frequency_mhz']} MHz")
            print(f"🎯 Best Diff:     {kpis['best_diff']:,}")
            print(f"📊 Session Diff:  {kpis['session_diff']:,}")
            print(f"✅ Accepted:      {kpis['accepted_shares']}")
            print(f"❌ Rejected:      {kpis['rejected_shares']}")
            print(f"⏰ Uptime:        {kpis['uptime_s']:,} seconds")
            print(f"📶 WiFi RSSI:     {kpis['wifi_rssi']} dBm")
            print(f"🏊 Pool:          {kpis['pool_url']}")
            print(f"👷 Worker:        {kpis['worker_name']}")
            print(f"🔧 ASIC Model:    {kpis['asic_model']}")
            print(f"🏗️  Board Ver:     {kpis['board_version']}")
            print(f"💾 Firmware:      {kpis['firmware_version']}")
    
    def run_monitor(self, show_detailed=False):
        """Main monitoring loop"""
        print(f"🚀 Starting Multi-Bitaxe Monitor")
        print(f"📊 Monitoring {len(self.miners)} miners:")
        for miner in self.miners:
            print(f"   - {miner['name']} ({miner['ip']})")
        print(f"📁 Data will be saved to: {self.csv_filename}")
        print(f"🔄 Polling every 30 seconds...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                all_kpis = self.collect_all_kpis()
                self.display_summary(all_kpis)
                
                if show_detailed:
                    self.display_detailed_kpis(all_kpis)
                
                self.log_to_csv(all_kpis)
                
                time.sleep(30)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Monitoring stopped by user")
            print(f"📁 Data saved to: {self.csv_filename}")
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    # Configuration - UPDATE THESE VALUES
    miners_config = [
        {'name': 'Gamma-1', 'ip': '192.168.1.45'},  # Replace with your miners' IPs
        {'name': 'Gamma-2', 'ip': '192.168.1.46'},  # Add/remove miners as needed
        {'name': 'Gamma-3', 'ip': '192.168.1.47'}   # Name can be anything you want
    ]
    
    # Create and run monitor
    # Set show_detailed=True to see individual miner details
    monitor = MultiBitaxeMonitor(miners_config)
    monitor.run_monitor(show_detailed=False)

if __name__ == "__main__":
    main()