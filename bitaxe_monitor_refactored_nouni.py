#!/usr/bin/env python3
"""
Multi-Bitaxe Gamma Miner KPI Monitor - Refactored Version (Python 3.6+ Compatible)
Polls multiple miners every 30 seconds for comprehensive performance metrics
"""

import requests
import time
import json
import csv
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MinerConfig:
    """Configuration for a single miner"""
    
    def __init__(self, name, ip, port=80):
        self.name = name
        self.ip = ip
        self.port = port

class ASICSpecs:
    """ASIC specifications for calculating expected hashrate"""
    
    # ASIC model specifications: (base_frequency_mhz, base_hashrate_gh)
    SPECS = {
        'BM1370': (600, 1200),  # Bitaxe Gamma: 1.2 TH/s at 600MHz
        'BM1368': (650, 700),   # Bitaxe Supra: 700 GH/s at ~650MHz  
        'BM1366': (525, 500),   # Bitaxe Ultra: 500 GH/s at ~525MHz
        'BM1397': (450, 400),   # Bitaxe Max: 400 GH/s at ~450MHz
    }
    
    @classmethod
    def calculate_expected_hashrate(cls, asic_model, frequency_mhz):
        """Calculate expected hashrate based on ASIC model and frequency"""
        if not asic_model or frequency_mhz <= 0:
            return 0
        
        # Find matching ASIC spec (handle variations in model naming)
        asic_key = None
        for model in cls.SPECS.keys():
            if model in asic_model.upper():
                asic_key = model
                break
        
        if not asic_key:
            # Try to detect based on hashrate range if model name doesn't match
            return cls._estimate_from_frequency(frequency_mhz)
        
        base_freq, base_hashrate = cls.SPECS[asic_key]
        
        # Linear scaling: expected_hashrate = base_hashrate * (current_freq / base_freq)
        expected_gh = base_hashrate * (frequency_mhz / base_freq)
        return max(0, expected_gh)
    
    @classmethod
    def _estimate_from_frequency(cls, frequency_mhz):
        """Fallback estimation based on frequency range"""
        if frequency_mhz >= 580:  # Likely BM1370 (Gamma)
            return 1200 * (frequency_mhz / 600)
        elif frequency_mhz >= 500:  # Likely BM1368 (Supra) or BM1366 (Ultra)
            return 600 * (frequency_mhz / 550)  # Conservative estimate
        else:  # Likely BM1397 (Max)
            return 400 * (frequency_mhz / 450)

class MinerMetrics:
    """Container for miner metrics"""
    
    def __init__(self, timestamp, miner_name, miner_ip, status='OFFLINE', **kwargs):
        self.timestamp = timestamp
        self.miner_name = miner_name
        self.miner_ip = miner_ip
        self.status = status
        
        # Performance metrics
        self.hashrate_gh = kwargs.get('hashrate_gh', 0.0)
        self.hashrate_th = kwargs.get('hashrate_th', 0.0)
        self.expected_hashrate_gh = kwargs.get('expected_hashrate_gh', 0.0)
        self.expected_hashrate_th = kwargs.get('expected_hashrate_th', 0.0)
        self.hashrate_efficiency_pct = kwargs.get('hashrate_efficiency_pct', 0.0)
        self.power_w = kwargs.get('power_w', 0.0)
        self.efficiency_jth = kwargs.get('efficiency_jth', 0.0)
        
        # Temperature and cooling
        self.temperature_c = kwargs.get('temperature_c', 0.0)
        self.vr_temperature_c = kwargs.get('vr_temperature_c', 0.0)
        self.fan_speed_rpm = kwargs.get('fan_speed_rpm', 0)
        
        # Voltage metrics
        self.core_voltage_actual_v = kwargs.get('core_voltage_actual_v', 0.0)
        self.core_voltage_set_v = kwargs.get('core_voltage_set_v', 0.0)
        self.input_voltage_v = kwargs.get('input_voltage_v', 0.0)
        
        # Frequency and difficulty
        self.frequency_mhz = kwargs.get('frequency_mhz', 0)
        self.best_diff = kwargs.get('best_diff', 0)
        self.session_diff = kwargs.get('session_diff', 0)
        
        # Shares and uptime
        self.accepted_shares = kwargs.get('accepted_shares', 0)
        self.rejected_shares = kwargs.get('rejected_shares', 0)
        self.uptime_s = kwargs.get('uptime_s', 0)
        
        # Network and pool
        self.wifi_rssi = kwargs.get('wifi_rssi', 0)
        self.pool_url = kwargs.get('pool_url', '')
        self.worker_name = kwargs.get('worker_name', '')
        
        # Hardware info
        self.asic_model = kwargs.get('asic_model', '')
        self.board_version = kwargs.get('board_version', '')
        self.firmware_version = kwargs.get('firmware_version', '')
    
    def to_dict(self):
        """Convert metrics to dictionary for CSV logging"""
        return {
            'timestamp': self.timestamp,
            'miner_name': self.miner_name,
            'miner_ip': self.miner_ip,
            'status': self.status,
            'hashrate_gh': self.hashrate_gh,
            'hashrate_th': self.hashrate_th,
            'expected_hashrate_gh': self.expected_hashrate_gh,
            'expected_hashrate_th': self.expected_hashrate_th,
            'hashrate_efficiency_pct': self.hashrate_efficiency_pct,
            'power_w': self.power_w,
            'efficiency_jth': self.efficiency_jth,
            'temperature_c': self.temperature_c,
            'vr_temperature_c': self.vr_temperature_c,
            'fan_speed_rpm': self.fan_speed_rpm,
            'core_voltage_actual_v': self.core_voltage_actual_v,
            'core_voltage_set_v': self.core_voltage_set_v,
            'input_voltage_v': self.input_voltage_v,
            'frequency_mhz': self.frequency_mhz,
            'best_diff': self.best_diff,
            'session_diff': self.session_diff,
            'accepted_shares': self.accepted_shares,
            'rejected_shares': self.rejected_shares,
            'uptime_s': self.uptime_s,
            'wifi_rssi': self.wifi_rssi,
            'pool_url': self.pool_url,
            'worker_name': self.worker_name,
            'asic_model': self.asic_model,
            'board_version': self.board_version,
            'firmware_version': self.firmware_version
        }
    
    @classmethod
    def get_csv_headers(cls):
        """Get CSV headers in the correct order"""
        return [
            'timestamp', 'miner_name', 'miner_ip', 'status',
            'hashrate_gh', 'hashrate_th', 'expected_hashrate_gh', 'expected_hashrate_th', 
            'hashrate_efficiency_pct', 'power_w', 'efficiency_jth',
            'temperature_c', 'vr_temperature_c', 'fan_speed_rpm',
            'core_voltage_actual_v', 'core_voltage_set_v', 'input_voltage_v',
            'frequency_mhz', 'best_diff', 'session_diff',
            'accepted_shares', 'rejected_shares', 'uptime_s',
            'wifi_rssi', 'pool_url', 'worker_name',
            'asic_model', 'board_version', 'firmware_version'
        ]

class BitaxeAPI:
    """Handles communication with Bitaxe API"""
    
    @staticmethod
    def get_system_info(miner_config, timeout=5):
        """Fetch system info from a miner"""
        try:
            url = "http://{}:{}/api/system/info".format(miner_config.ip, miner_config.port)
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch data from {} ({}): {}".format(
                miner_config.name, miner_config.ip, e))
            return None

class MetricsCollector:
    """Collects and processes miner metrics"""
    
    def __init__(self, expected_hashrates=None):
        """
        Initialize collector
        
        Args:
            expected_hashrates: Optional dict of miner_name -> expected_gh overrides
        """
        self.api = BitaxeAPI()
        self.expected_hashrates = expected_hashrates or {}
    
    def collect_miner_metrics(self, miner_config):
        """Collect comprehensive metrics from a single miner"""
        timestamp = datetime.now().isoformat()
        
        # Get system data
        system_data = self.api.get_system_info(miner_config)
        
        if not system_data:
            return self._create_offline_metrics(miner_config, timestamp)
        
        return self._parse_system_data(miner_config, timestamp, system_data)
    
    def _create_offline_metrics(self, miner_config, timestamp):
        """Create metrics object for offline miner"""
        return MinerMetrics(
            timestamp=timestamp,
            miner_name=miner_config.name,
            miner_ip=miner_config.ip,
            status='OFFLINE'
        )
    
    def _parse_system_data(self, miner_config, timestamp, data):
        """Parse system data into metrics object"""
        # Extract hashrate and convert units
        hashrate_gh = data.get('hashRate', 0)  # Already in GH/s
        hashrate_th = hashrate_gh / 1000  # Convert GH/s to TH/s
        
        # Get ASIC model and frequency for expected hashrate calculation
        asic_model = data.get('ASICModel', '')
        frequency_mhz = data.get('frequency', 0)
        
        # Calculate expected hashrate based on ASIC specs and frequency
        expected_hashrate_gh = ASICSpecs.calculate_expected_hashrate(asic_model, frequency_mhz)
        
        # Check for manual override
        if miner_config.name in self.expected_hashrates:
            expected_hashrate_gh = self.expected_hashrates[miner_config.name]
        
        expected_hashrate_th = expected_hashrate_gh / 1000
        
        # Calculate hashrate efficiency percentage
        hashrate_efficiency_pct = 0
        if expected_hashrate_gh > 0:
            hashrate_efficiency_pct = (hashrate_gh / expected_hashrate_gh) * 100
        
        # Extract power metrics
        power_w = data.get('power', 0)
        
        # Calculate efficiency
        efficiency_jth = (power_w / hashrate_th) if hashrate_th > 0 else 0
        
        # Extract voltage metrics (convert mV to V)
        core_voltage_actual = data.get('coreVoltageActual', 0) / 1000
        core_voltage_set = data.get('coreVoltage', 0) / 1000  # This is the set voltage
        input_voltage = data.get('voltage', 0) / 1000
        
        return MinerMetrics(
            timestamp=timestamp,
            miner_name=miner_config.name,
            miner_ip=miner_config.ip,
            status='ONLINE',
            hashrate_gh=hashrate_gh,
            hashrate_th=hashrate_th,
            expected_hashrate_gh=expected_hashrate_gh,
            expected_hashrate_th=expected_hashrate_th,
            hashrate_efficiency_pct=hashrate_efficiency_pct,
            power_w=power_w,
            efficiency_jth=efficiency_jth,
            temperature_c=data.get('temp', 0),
            vr_temperature_c=data.get('vrTemp', 0),
            fan_speed_rpm=data.get('fanrpm', 0),
            core_voltage_actual_v=core_voltage_actual,
            core_voltage_set_v=core_voltage_set,
            input_voltage_v=input_voltage,
            frequency_mhz=data.get('frequency', 0),
            best_diff=data.get('bestNonceDiff', 0),
            session_diff=data.get('bestSessionNonceDiff', 0),
            accepted_shares=data.get('sharesAccepted', 0),
            rejected_shares=data.get('sharesRejected', 0),
            uptime_s=data.get('uptimeSeconds', 0),
            wifi_rssi=data.get('wifiRSSI', 0),
            pool_url=data.get('stratumURL', ''),
            worker_name=data.get('stratumUser', ''),
            asic_model=data.get('ASICModel', ''),
            board_version=data.get('boardVersion', ''),
            firmware_version=data.get('version', '')
        )
    
    def collect_all_metrics(self, miners):
        """Collect metrics from all miners concurrently"""
        all_metrics = []
        
        with ThreadPoolExecutor(max_workers=len(miners)) as executor:
            future_to_miner = {
                executor.submit(self.collect_miner_metrics, miner): miner 
                for miner in miners
            }
            
            for future in as_completed(future_to_miner):
                miner = future_to_miner[future]
                try:
                    metrics = future.result()
                    all_metrics.append(metrics)
                except Exception as e:
                    logger.error("Exception collecting metrics from {}: {}".format(miner.name, e))
                    all_metrics.append(self._create_offline_metrics(
                        miner, 
                        datetime.now().isoformat()
                    ))
        
        return sorted(all_metrics, key=lambda x: x.miner_name)

class DataLogger:
    """Handles CSV logging of metrics"""
    
    def __init__(self, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = "multi_bitaxe_kpis_{}.csv".format(timestamp)
        
        self.filename = filename
        self._setup_csv()
    
    def _setup_csv(self):
        """Setup CSV file with headers"""
        if not os.path.exists(self.filename):
            headers = MinerMetrics.get_csv_headers()
            
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def log_metrics(self, metrics_list):
        """Log metrics to CSV file"""
        if not metrics_list:
            return
        
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            for metrics in metrics_list:
                # Convert metrics to ordered list of values
                data_dict = metrics.to_dict()
                headers = MinerMetrics.get_csv_headers()
                row = [data_dict[header] for header in headers]
                writer.writerow(row)

class Display:
    """Handles console output and display formatting"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def show_summary(metrics_list):
        """Display summary table of all miners"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("\n{} Multi-Bitaxe Summary - {}".format(FIRE_EMOJI, timestamp))
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
                # Format efficiency with icon
                if metrics.expected_hashrate_gh > 0:
                    eff_pct = metrics.hashrate_efficiency_pct
                    if eff_pct >= 95:
                        eff_display = "{:3.0f}{}".format(eff_pct, FIRE_EMOJI)
                    elif eff_pct >= 85:
                        eff_display = "{:3.0f}{}".format(eff_pct, LIGHTNING_EMOJI)
                    elif eff_pct < 70:
                        eff_display = "{:3.0f}{}".format(eff_pct, WARNING_EMOJI)
                    else:
                        eff_display = "{:3.0f}%".format(eff_pct)
                else:
                    eff_display = "N/A"
                
                print(" {} {:<7} {:>7.3f}   {:>3.0f}W  {:>4}MHz {:>5.3f}V {:>5.1f}  {:<6} {:>5.2f}  {:>4.0f}".format(
                    GREEN_DOT,
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
                print(" {} {:<7} OFFLINE".format(RED_DOT, metrics.miner_name))
        
        print("-" * 75)
        
        if online_count > 0:
            avg_efficiency_jth = total_power / total_hashrate_th if total_hashrate_th > 0 else 0
            avg_temp = sum(m.temperature_c for m in metrics_list if m.status == 'ONLINE') / online_count
            avg_fan = sum(m.fan_speed_rpm for m in metrics_list if m.status == 'ONLINE') / online_count
            
            if total_expected_th > 0:
                fleet_efficiency = (total_hashrate_th / total_expected_th * 100)
                if fleet_efficiency >= 95:
                    fleet_eff_display = "{:3.0f}{}".format(fleet_efficiency, FIRE_EMOJI)
                elif fleet_efficiency >= 85:
                    fleet_eff_display = "{:3.0f}{}".format(fleet_efficiency, LIGHTNING_EMOJI)
                else:
                    fleet_eff_display = "{:3.0f}%".format(fleet_efficiency)
            else:
                fleet_eff_display = "N/A"
            
            print(" {} TOTALS   {:>7.3f}   {:>3.0f}W    ---   ---   {:>5.1f}  {:<6} {:>5.2f}  {:>4.0f}".format(
                CHART_EMOJI,
                total_hashrate_th,
                total_power,
                avg_efficiency_jth,
                fleet_eff_display,
                avg_temp,
                avg_fan
            ))
        else:
            print(" {} ALL OFF".format(CROSS_EMOJI))
        
        print("=" * 85)
        print()
        
        # Additional info in a simple format
        if online_count > 0:
            print("{} Additional Info:".format(CHART_EMOJI))
            for metrics in metrics_list:
                if metrics.status == 'ONLINE':
                    print("   {}: VR:{:.1f}°C  ActV:{:.3f}V  InV:{:.2f}V  Pool:{}".format(
                        metrics.miner_name,
                        metrics.vr_temperature_c,
                        metrics.core_voltage_actual_v, 
                        metrics.input_voltage_v,
                        metrics.pool_url.split('/')[-1] if metrics.pool_url else 'N/A'
                    ))
            print()
        
        # Show calculation method
        if online_count > 0:
            sample_asic = next((m.asic_model for m in metrics_list if m.status == 'ONLINE'), 'Unknown')
            print("{} Expected hashrate from {} specs + frequency".format(BULB_EMOJI, sample_asic))
            print()
    
    @staticmethod
    def show_detailed(metrics_list):
        """Display detailed metrics for each online miner"""
        for metrics in metrics_list:
            if metrics.status != 'ONLINE':
                continue
            
            print("\n🔥 {} ({}) - {}".format(
                metrics.miner_name, metrics.miner_ip, metrics.timestamp[:19]))
            print("=" * 60)
            print("⚡ Hashrate:        {:.2f} GH/s ({:.3f} TH/s)".format(
                metrics.hashrate_gh, metrics.hashrate_th))
            if metrics.expected_hashrate_gh > 0:
                print("🎯 Expected:        {:.2f} GH/s ({:.3f} TH/s) - {:.1f}% efficiency".format(
                    metrics.expected_hashrate_gh, metrics.expected_hashrate_th, metrics.hashrate_efficiency_pct))
            print("🔌 Power:           {:.1f} W".format(metrics.power_w))
            print("⚙️  Efficiency:      {:.1f} J/TH".format(metrics.efficiency_jth))
            print("🌡️  Temperature:     {:.1f}°C (ASIC) / {:.1f}°C (VR)".format(
                metrics.temperature_c, metrics.vr_temperature_c))
            print("💨 Fan Speed:       {} RPM".format(metrics.fan_speed_rpm))
            print("⚡ Core Voltage:    {:.3f}V (Set) / {:.3f}V (Actual)".format(
                metrics.core_voltage_set_v, metrics.core_voltage_actual_v))
            print("🔋 Input Voltage:   {:.2f}V".format(metrics.input_voltage_v))
            print("📡 Frequency:       {} MHz".format(metrics.frequency_mhz))
            print("🎯 Best Diff:       {:,}".format(metrics.best_diff))
            print("📊 Session Diff:    {:,}".format(metrics.session_diff))
            print("✅ Accepted:        {}".format(metrics.accepted_shares))
            print("❌ Rejected:        {}".format(metrics.rejected_shares))
            print("⏰ Uptime:          {:,} seconds".format(metrics.uptime_s))
            print("📶 WiFi RSSI:       {} dBm".format(metrics.wifi_rssi))
            print("🏊 Pool:            {}".format(metrics.pool_url))
            print("👷 Worker:          {}".format(metrics.worker_name))
            print("🔧 ASIC Model:      {}".format(metrics.asic_model))
            print("🏗️  Board Version:   {}".format(metrics.board_version))
            print("💾 Firmware:        {}".format(metrics.firmware_version))

class MultiBitaxeMonitor:
    """Main monitor class that orchestrates the monitoring process"""
    
    def __init__(self, miners_config, poll_interval=30, expected_hashrates=None):
        """
        Initialize monitor
        
        Args:
            miners_config: List of miner configurations
            poll_interval: Seconds between polls (default 30)
            expected_hashrates: Optional dict of miner_name -> expected_gh overrides
                Example: {'Gamma-1': 1200, 'Gamma-2': 1150}
        """
        self.miners = [MinerConfig(**config) for config in miners_config]
        self.poll_interval = poll_interval
        self.expected_hashrates = expected_hashrates or {}
        self.collector = MetricsCollector(self.expected_hashrates)
        self.logger = DataLogger()
        self.display = Display()
    
    def run_monitor(self, show_detailed=False):
        """Main monitoring loop"""
        print("🚀 Starting Multi-Bitaxe Monitor")
        print("📊 Monitoring {} miners:".format(len(self.miners)))
        for miner in self.miners:
            print("   - {} ({}:{})".format(miner.name, miner.ip, miner.port))
        print("📁 Data will be saved to: {}".format(self.logger.filename))
        print("🔄 Polling every {} seconds...".format(self.poll_interval))
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                start_time = time.time()
                
                # Collect metrics from all miners
                all_metrics = self.collector.collect_all_metrics(self.miners)
                
                # Display results
                self.display.show_summary(all_metrics)
                
                if show_detailed:
                    self.display.show_detailed(all_metrics)
                
                # Log to CSV
                self.logger.log_metrics(all_metrics)
                
                # Calculate sleep time to maintain consistent intervals
                elapsed = time.time() - start_time
                sleep_time = max(0, self.poll_interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    logger.warning("Collection took {:.1f}s, longer than {}s interval".format(
                        elapsed, self.poll_interval))
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            print("📁 Data saved to: {}".format(self.logger.filename))
        except Exception as e:
            logger.error("Monitoring error: {}".format(e))
            print("📁 Data saved to: {}".format(self.logger.filename))

def main():
    """Main entry point"""
    # Configuration - UPDATE THESE VALUES FOR YOUR MINERS
    miners_config = [
        {'name': 'Gamma-1', 'ip': '192.168.1.45'},
        {'name': 'Gamma-2', 'ip': '192.168.1.46'},
        {'name': 'Gamma-3', 'ip': '192.168.1.47'}
        # Add more miners as needed:
        # {'name': 'Gamma-4', 'ip': '192.168.1.48', 'port': 8080},  # Custom port example
    ]
    
    # Optional: Manual expected hashrate overrides (in GH/s)
    # Leave empty {} to use automatic calculation based on ASIC model + frequency
    expected_hashrates = {
        # 'Gamma-1': 1200,  # Force expected hashrate to 1200 GH/s
        # 'Gamma-2': 1150,  # Force expected hashrate to 1150 GH/s
        # 'Gamma-3': 1100,  # Force expected hashrate to 1100 GH/s
    }
    
    # Create and run monitor
    monitor = MultiBitaxeMonitor(
        miners_config=miners_config,
        poll_interval=30,  # 30 seconds between polls
        expected_hashrates=expected_hashrates
    )
    
    # Set show_detailed=True to see individual miner details
    monitor.run_monitor(show_detailed=False)

if __name__ == "__main__":
    main()