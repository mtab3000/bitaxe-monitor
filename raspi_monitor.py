#!/usr/bin/env python3
"""
Raspberry Pi Compatible Bitaxe Monitor
Simple ASCII-only version guaranteed to work on any terminal
"""

import requests
import time
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Configuration - UPDATE THESE WITH YOUR MINER IPS
miners_config = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45'},
    {'name': 'Gamma-2', 'ip': '192.168.1.46'},
    {'name': 'Gamma-3', 'ip': '192.168.1.47'},
]

class ASICSpecs:
    """ASIC specifications for hashrate calculations"""
    SPECS = {
        'BM1370': {'base_hashrate_gh': 1200, 'base_frequency_mhz': 600},
        'BM1368': {'base_hashrate_gh': 700, 'base_frequency_mhz': 650},
        'BM1366': {'base_hashrate_gh': 500, 'base_frequency_mhz': 525},
        'BM1397': {'base_hashrate_gh': 400, 'base_frequency_mhz': 450},
    }
    
    @classmethod
    def get_expected_hashrate(cls, asic_model, frequency_mhz):
        """Calculate expected hashrate based on ASIC model and frequency"""
        if asic_model not in cls.SPECS:
            return 0
        
        spec = cls.SPECS[asic_model]
        scaling_factor = frequency_mhz / spec['base_frequency_mhz']
        return spec['base_hashrate_gh'] * scaling_factor

class MinerMetrics:
    """Container for miner metrics data"""
    def __init__(self, miner_name, miner_ip):
        self.miner_name = miner_name
        self.miner_ip = miner_ip
        self.timestamp = datetime.now()
        self.status = 'OFFLINE'
        
        # Core metrics
        self.hashrate_gh = 0
        self.hashrate_th = 0
        self.power_w = 0
        self.efficiency_jth = 0
        self.temperature_c = 0
        self.fan_speed_rpm = 0
        
        # Voltage metrics
        self.core_voltage_set_v = 0
        self.core_voltage_actual_v = 0
        self.input_voltage_v = 0
        self.vr_temperature_c = 0
        
        # Frequency and ASIC info
        self.frequency_mhz = 0
        self.asic_model = ''
        
        # Expected hashrate and efficiency
        self.expected_hashrate_gh = 0
        self.expected_hashrate_th = 0
        self.hashrate_efficiency_pct = 0
        
        # Network and pool info
        self.pool_url = ''
        self.accepted_shares = 0
        self.rejected_shares = 0

class MultiBitaxeMonitor:
    """Main monitoring class for multiple Bitaxe miners"""
    
    def __init__(self, miners_config, poll_interval=30):
        self.miners_config = miners_config
        self.poll_interval = poll_interval
        
        # CSV setup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.csv_filename = f'multi_bitaxe_kpis_{timestamp}.csv'
        self.csv_headers_written = False
        
        print(">>> Multi-Bitaxe Monitor v2.0 (Raspberry Pi Edition)")
        print("Configuration: {} miners".format(len(miners_config)))
        
    def fetch_miner_data(self, miner_config):
        """Fetch data from a single miner"""
        metrics = MinerMetrics(miner_config['name'], miner_config['ip'])
        
        try:
            port = miner_config.get('port', 80)
            url = f"http://{miner_config['ip']}:{port}/api/system/info"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract metrics
            metrics.status = 'ONLINE'
            metrics.hashrate_gh = float(data.get('hashRate', 0)) / 1000
            metrics.hashrate_th = metrics.hashrate_gh / 1000
            metrics.power_w = float(data.get('power', 0))
            metrics.temperature_c = float(data.get('temp', 0))
            metrics.fan_speed_rpm = float(data.get('fanSpeed', 0))
            
            # Voltage metrics
            metrics.core_voltage_set_v = float(data.get('coreVoltage', 0)) / 1000
            metrics.core_voltage_actual_v = float(data.get('coreVoltageActual', 0)) / 1000
            metrics.input_voltage_v = float(data.get('voltage', 0))
            metrics.vr_temperature_c = float(data.get('vrTemp', 0))
            
            # Frequency and ASIC
            metrics.frequency_mhz = int(data.get('frequency', 0))
            metrics.asic_model = data.get('ASICModel', 'Unknown')
            
            # Pool info
            metrics.pool_url = data.get('poolURL', '')
            metrics.accepted_shares = int(data.get('sharesAccepted', 0))
            metrics.rejected_shares = int(data.get('sharesRejected', 0))
            
            # Calculate efficiency
            if metrics.power_w > 0:
                metrics.efficiency_jth = metrics.power_w / metrics.hashrate_th if metrics.hashrate_th > 0 else 0
            
            # Calculate expected hashrate and efficiency
            metrics.expected_hashrate_gh = ASICSpecs.get_expected_hashrate(
                metrics.asic_model, metrics.frequency_mhz)
            metrics.expected_hashrate_th = metrics.expected_hashrate_gh / 1000
            
            if metrics.expected_hashrate_gh > 0:
                metrics.hashrate_efficiency_pct = (metrics.hashrate_gh / metrics.expected_hashrate_gh) * 100
            
        except Exception as e:
            print("Error fetching data from {}: {}".format(miner_config['name'], str(e)))
            
        return metrics
    
    def collect_all_metrics(self):
        """Collect metrics from all miners concurrently"""
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.fetch_miner_data, config) 
                      for config in self.miners_config]
            return [future.result() for future in futures]
    
    def save_to_csv(self, metrics_list):
        """Save metrics to CSV file"""
        if not metrics_list:
            return
            
        # CSV headers
        headers = [
            'timestamp', 'miner_name', 'miner_ip', 'status',
            'hashrate_gh', 'hashrate_th', 'expected_hashrate_gh', 'expected_hashrate_th',
            'hashrate_efficiency_pct', 'power_w', 'efficiency_jth',
            'temperature_c', 'vr_temperature_c', 'fan_speed_rpm',
            'core_voltage_set_v', 'core_voltage_actual_v', 'input_voltage_v',
            'frequency_mhz', 'asic_model', 'pool_url',
            'accepted_shares', 'rejected_shares'
        ]
        
        with open(self.csv_filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            
            if not self.csv_headers_written:
                writer.writeheader()
                self.csv_headers_written = True
            
            for metrics in metrics_list:
                row = {
                    'timestamp': metrics.timestamp.isoformat(),
                    'miner_name': metrics.miner_name,
                    'miner_ip': metrics.miner_ip,
                    'status': metrics.status,
                    'hashrate_gh': metrics.hashrate_gh,
                    'hashrate_th': metrics.hashrate_th,
                    'expected_hashrate_gh': metrics.expected_hashrate_gh,
                    'expected_hashrate_th': metrics.expected_hashrate_th,
                    'hashrate_efficiency_pct': metrics.hashrate_efficiency_pct,
                    'power_w': metrics.power_w,
                    'efficiency_jth': metrics.efficiency_jth,
                    'temperature_c': metrics.temperature_c,
                    'vr_temperature_c': metrics.vr_temperature_c,
                    'fan_speed_rpm': metrics.fan_speed_rpm,
                    'core_voltage_set_v': metrics.core_voltage_set_v,
                    'core_voltage_actual_v': metrics.core_voltage_actual_v,
                    'input_voltage_v': metrics.input_voltage_v,
                    'frequency_mhz': metrics.frequency_mhz,
                    'asic_model': metrics.asic_model,
                    'pool_url': metrics.pool_url,
                    'accepted_shares': metrics.accepted_shares,
                    'rejected_shares': metrics.rejected_shares,
                }
                writer.writerow(row)
    
    @staticmethod
    def show_summary(metrics_list):
        """Display summary table of all miners"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("\n!! Multi-Bitaxe Summary - {}".format(timestamp))
        print("=" * 85)
        
        # Simple, clean table with fixed widths
        print(" Miner     Hash(TH)  Power  FREQ    SET V   J/TH  Eff%   Temp   Fan")
        print("-" * 75)
        
        total_hashrate_th = 0
        total_expected_th = 0
        total_power = 0
        online_count = 0
        
        for metrics in metrics_list:
            if metrics.status == 'ONLINE':
                # Format efficiency with simple text indicators
                if metrics.expected_hashrate_gh > 0:
                    eff_pct = metrics.hashrate_efficiency_pct
                    if eff_pct >= 95:
                        eff_display = "{:3.0f}!!".format(eff_pct)
                    elif eff_pct >= 85:
                        eff_display = "{:3.0f}*".format(eff_pct)
                    elif eff_pct < 70:
                        eff_display = "{:3.0f}!!".format(eff_pct)
                    else:
                        eff_display = "{:3.0f}%".format(eff_pct)
                else:
                    eff_display = "N/A"
                
                print(" [ON] {:<7} {:>7.3f}   {:>3.0f}W  {:>4}MHz {:>5.3f}V {:>5.1f}  {:<6} {:>5.2f}  {:>4.0f}".format(
                    metrics.miner_name,
                    metrics.hashrate_th,
                    metrics.power_w,
                    metrics.frequency_mhz,
                    metrics.core_voltage_set_v,
                    metrics.efficiency_jth,
                    eff_display,
                    metrics.temperature_c,
                    metrics.fan_speed_rpm
                ))
                
                total_hashrate_th += metrics.hashrate_th
                total_expected_th += metrics.expected_hashrate_th
                total_power += metrics.power_w
                online_count += 1
            else:
                print(" [OFF] {:<7} OFFLINE".format(metrics.miner_name))
        
        print("-" * 75)
        
        if online_count > 0:
            avg_efficiency_jth = total_power / total_hashrate_th if total_hashrate_th > 0 else 0
            avg_temp = sum(m.temperature_c for m in metrics_list if m.status == 'ONLINE') / online_count
            avg_fan = sum(m.fan_speed_rpm for m in metrics_list if m.status == 'ONLINE') / online_count
            
            if total_expected_th > 0:
                fleet_efficiency = (total_hashrate_th / total_expected_th * 100)
                if fleet_efficiency >= 95:
                    fleet_eff_display = "{:3.0f}!!".format(fleet_efficiency)
                elif fleet_efficiency >= 85:
                    fleet_eff_display = "{:3.0f}*".format(fleet_efficiency)
                else:
                    fleet_eff_display = "{:3.0f}%".format(fleet_efficiency)
            else:
                fleet_eff_display = "N/A"
            
            print(" [#] TOTALS   {:>7.3f}   {:>3.0f}W    ---   ---   {:>5.1f}  {:<6} {:>5.2f}  {:>4.0f}".format(
                total_hashrate_th,
                total_power,
                avg_efficiency_jth,
                fleet_eff_display,
                avg_temp,
                avg_fan
            ))
        else:
            print(" [X] ALL OFF")
        
        print("=" * 85)
        print("")
        
        # Additional info in a simple format
        if online_count > 0:
            print("[#] Additional Info:")
            for metrics in metrics_list:
                if metrics.status == 'ONLINE':
                    print("   {}: VR:{:.1f}C  ActV:{:.3f}V  InV:{:.2f}V  Pool:{}".format(
                        metrics.miner_name,
                        metrics.vr_temperature_c,
                        metrics.core_voltage_actual_v, 
                        metrics.input_voltage_v,
                        metrics.pool_url.split('/')[-1] if metrics.pool_url else 'N/A'
                    ))
            print("")
        
        # Show calculation method
        if online_count > 0:
            sample_asic = next((m.asic_model for m in metrics_list if m.status == 'ONLINE'), 'Unknown')
            print("[i] Expected hashrate from {} specs + frequency".format(sample_asic))
            print("")
    
    def run_monitor(self):
        """Main monitoring loop"""
        print("\n>>> Starting Multi-Bitaxe Monitor")
        print("Configuration: {} miners, {}s intervals".format(len(self.miners_config), self.poll_interval))
        print("=" * 60)
        
        try:
            while True:
                start_time = time.time()
                
                # Collect metrics from all miners
                metrics_list = self.collect_all_metrics()
                
                # Display results
                self.show_summary(metrics_list)
                
                # Save to CSV
                self.save_to_csv(metrics_list)
                
                # Calculate and display timing
                collection_time = time.time() - start_time
                if collection_time > 30:
                    print("!! Warning: Collection took {:.1f}s (>30s)".format(collection_time))
                
                print("Data collected in {:.1f}s | Next update in {}s | Ctrl+C to stop".format(
                    collection_time, self.poll_interval))
                
                # Wait for next poll
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\n>>> Monitor stopped by user")
            print("CSV file saved: {}".format(self.csv_filename))

def main():
    """Main function"""
    monitor = MultiBitaxeMonitor(
        miners_config=miners_config,
        poll_interval=30
    )
    monitor.run_monitor()

if __name__ == "__main__":
    main()
