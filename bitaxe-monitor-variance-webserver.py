#!/usr/bin/env python3
"""
Multi-Bitaxe Monitor - With Variance Tracking and Web Interface

A comprehensive monitoring solution for Bitaxe mining devices with real-time metrics,
variance tracking, and web interface.

Features:
- Multi-miner support with concurrent polling
- Real-time hashrate variance tracking (60s, 300s, 600s windows)
- Web dashboard accessible on LAN
- CSV data logging for historical analysis
- Automatic ASIC model detection and expected hashrate calculation
- Visual alerts for efficiency and variance issues

Author: mtab3000
License: MIT
"""

import requests
import time
import json
import csv
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from collections import deque, defaultdict
import statistics
import threading
from flask import Flask, render_template_string, jsonify
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress Flask logging in production
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

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

class HashrateHistory:
    """Manages historical hashrate data for variance calculations"""
    
    def __init__(self):
        # Store tuples of (timestamp, hashrate_gh) for each miner
        self.history = defaultdict(deque)
        self.max_history_seconds = 600  # Keep 10 minutes of history
    
    def add_sample(self, miner_name, timestamp, hashrate_gh):
        """Add a hashrate sample for a miner"""
        history = self.history[miner_name]
        
        # Convert timestamp string to datetime if needed
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # Add new sample
        history.append((timestamp, hashrate_gh))
        
        # Remove old samples beyond max history
        cutoff_time = timestamp - timedelta(seconds=self.max_history_seconds)
        while history and history[0][0] < cutoff_time:
            history.popleft()
    
    def calculate_variance(self, miner_name, window_seconds):
        """Calculate hashrate variance over specified window"""
        history = self.history.get(miner_name, deque())
        if not history:
            return None
        
        # Get current time from most recent sample
        current_time = history[-1][0]
        cutoff_time = current_time - timedelta(seconds=window_seconds)
        
        # Collect samples within window
        samples = []
        for timestamp, hashrate in history:
            if timestamp >= cutoff_time:
                samples.append(hashrate)
        
        # Need at least 2 samples for variance
        if len(samples) < 2:
            return None
        
        # Calculate variance
        try:
            variance = statistics.variance(samples)
            return variance
        except:
            return None
    
    def calculate_std_dev(self, miner_name, window_seconds):
        """Calculate hashrate standard deviation over specified window"""
        variance = self.calculate_variance(miner_name, window_seconds)
        if variance is None:
            return None
        return variance ** 0.5
    
    def get_sample_count(self, miner_name, window_seconds):
        """Get number of samples in specified window"""
        history = self.history.get(miner_name, deque())
        if not history:
            return 0
        
        current_time = history[-1][0]
        cutoff_time = current_time - timedelta(seconds=window_seconds)
        
        count = sum(1 for timestamp, _ in history if timestamp >= cutoff_time)
        return count
    
    def get_history_data(self, miner_name, window_seconds=600):
        """Get historical data for charting"""
        history = self.history.get(miner_name, deque())
        if not history:
            return []
        
        current_time = history[-1][0]
        cutoff_time = current_time - timedelta(seconds=window_seconds)
        
        data = []
        for timestamp, hashrate in history:
            if timestamp >= cutoff_time:
                data.append({
                    'time': timestamp.isoformat(),
                    'hashrate': hashrate
                })
        
        return data

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
        
        # Variance metrics (new)
        self.hashrate_variance_60s = kwargs.get('hashrate_variance_60s', None)
        self.hashrate_variance_300s = kwargs.get('hashrate_variance_300s', None)
        self.hashrate_variance_600s = kwargs.get('hashrate_variance_600s', None)
        self.hashrate_stddev_60s = kwargs.get('hashrate_stddev_60s', None)
        self.hashrate_stddev_300s = kwargs.get('hashrate_stddev_300s', None)
        self.hashrate_stddev_600s = kwargs.get('hashrate_stddev_600s', None)
        
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
            'hashrate_variance_60s': self.hashrate_variance_60s if self.hashrate_variance_60s is not None else '',
            'hashrate_variance_300s': self.hashrate_variance_300s if self.hashrate_variance_300s is not None else '',
            'hashrate_variance_600s': self.hashrate_variance_600s if self.hashrate_variance_600s is not None else '',
            'hashrate_stddev_60s': self.hashrate_stddev_60s if self.hashrate_stddev_60s is not None else '',
            'hashrate_stddev_300s': self.hashrate_stddev_300s if self.hashrate_stddev_300s is not None else '',
            'hashrate_stddev_600s': self.hashrate_stddev_600s if self.hashrate_stddev_600s is not None else '',
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
    
    def to_web_dict(self):
        """Convert metrics to dictionary for web display"""
        return {
            'timestamp': self.timestamp,
            'miner_name': self.miner_name,
            'miner_ip': self.miner_ip,
            'status': self.status,
            'hashrate_gh': round(self.hashrate_gh, 2),
            'hashrate_th': round(self.hashrate_th, 3),
            'expected_hashrate_gh': round(self.expected_hashrate_gh, 2),
            'expected_hashrate_th': round(self.expected_hashrate_th, 3),
            'hashrate_efficiency_pct': round(self.hashrate_efficiency_pct, 1),
            'hashrate_stddev_60s': round(self.hashrate_stddev_60s, 1) if self.hashrate_stddev_60s is not None else None,
            'hashrate_stddev_300s': round(self.hashrate_stddev_300s, 1) if self.hashrate_stddev_300s is not None else None,
            'hashrate_stddev_600s': round(self.hashrate_stddev_600s, 1) if self.hashrate_stddev_600s is not None else None,
            'power_w': round(self.power_w, 1),
            'efficiency_jth': round(self.efficiency_jth, 1),
            'temperature_c': round(self.temperature_c, 1),
            'vr_temperature_c': round(self.vr_temperature_c, 1),
            'fan_speed_rpm': self.fan_speed_rpm,
            'core_voltage_actual_v': round(self.core_voltage_actual_v, 3),
            'core_voltage_set_v': round(self.core_voltage_set_v, 3),
            'input_voltage_v': round(self.input_voltage_v, 2),
            'frequency_mhz': self.frequency_mhz,
            'best_diff': self.best_diff,
            'session_diff': self.session_diff,
            'accepted_shares': self.accepted_shares,
            'rejected_shares': self.rejected_shares,
            'uptime_s': self.uptime_s,
            'uptime_formatted': self._format_uptime(),
            'wifi_rssi': self.wifi_rssi,
            'pool_url': self.pool_url,
            'worker_name': self.worker_name,
            'asic_model': self.asic_model,
            'board_version': self.board_version,
            'firmware_version': self.firmware_version
        }
    
    def _format_uptime(self):
        """Format uptime in human-readable format"""
        if self.uptime_s == 0:
            return "0s"
        
        days = self.uptime_s // 86400
        hours = (self.uptime_s % 86400) // 3600
        minutes = (self.uptime_s % 3600) // 60
        
        parts = []
        if days > 0:
            parts.append("{}d".format(days))
        if hours > 0:
            parts.append("{}h".format(hours))
        if minutes > 0:
            parts.append("{}m".format(minutes))
        
        return " ".join(parts) if parts else "<1m"
    
    @classmethod
    def get_csv_headers(cls):
        """Get CSV headers in the correct order"""
        return [
            'timestamp', 'miner_name', 'miner_ip', 'status',
            'hashrate_gh', 'hashrate_th', 'expected_hashrate_gh', 'expected_hashrate_th', 
            'hashrate_efficiency_pct',
            'hashrate_variance_60s', 'hashrate_variance_300s', 'hashrate_variance_600s',
            'hashrate_stddev_60s', 'hashrate_stddev_300s', 'hashrate_stddev_600s',
            'power_w', 'efficiency_jth',
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
        self.hashrate_history = HashrateHistory()
        self.latest_metrics = []  # Store latest metrics for web display
        self.metrics_lock = threading.Lock()
    
    def collect_miner_metrics(self, miner_config):
        """Collect comprehensive metrics from a single miner"""
        timestamp = datetime.now()
        timestamp_str = timestamp.isoformat()
        
        # Get system data
        system_data = self.api.get_system_info(miner_config)
        
        if not system_data:
            return self._create_offline_metrics(miner_config, timestamp_str)
        
        metrics = self._parse_system_data(miner_config, timestamp_str, system_data)
        
        # Add hashrate sample to history and calculate variance
        if metrics.status == 'ONLINE':
            self.hashrate_history.add_sample(miner_config.name, timestamp, metrics.hashrate_gh)
            
            # Calculate variance for different windows
            metrics.hashrate_variance_60s = self.hashrate_history.calculate_variance(miner_config.name, 60)
            metrics.hashrate_variance_300s = self.hashrate_history.calculate_variance(miner_config.name, 300)
            metrics.hashrate_variance_600s = self.hashrate_history.calculate_variance(miner_config.name, 600)
            
            # Calculate standard deviation
            metrics.hashrate_stddev_60s = self.hashrate_history.calculate_std_dev(miner_config.name, 60)
            metrics.hashrate_stddev_300s = self.hashrate_history.calculate_std_dev(miner_config.name, 300)
            metrics.hashrate_stddev_600s = self.hashrate_history.calculate_std_dev(miner_config.name, 600)
        
        return metrics
    
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
        
        sorted_metrics = sorted(all_metrics, key=lambda x: x.miner_name)
        
        # Store latest metrics for web display
        with self.metrics_lock:
            self.latest_metrics = sorted_metrics
        
        return sorted_metrics
    
    def get_latest_metrics(self):
        """Get latest metrics for web display"""
        with self.metrics_lock:
            return self.latest_metrics.copy()
    
    def get_history_data(self, miner_name, window_seconds=600):
        """Get historical data for a specific miner"""
        return self.hashrate_history.get_history_data(miner_name, window_seconds)

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
        print("\n🔥 Multi-Bitaxe Summary - {}".format(timestamp))
        print("=" * 105)
        
        # Enhanced table with variance info
        print(" Miner     Hash(TH)  Power  FREQ    SET V   J/TH  Eff%   Temp   Fan    σ60s   σ300s  σ600s")
        print("-" * 105)
        
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
                        eff_display = "{:3.0f}🔥".format(eff_pct)
                    elif eff_pct >= 85:
                        eff_display = "{:3.0f}⚡".format(eff_pct)
                    elif eff_pct < 70:
                        eff_display = "{:3.0f}⚠️".format(eff_pct)
                    else:
                        eff_display = "{:3.0f}%".format(eff_pct)
                else:
                    eff_display = "N/A"
                
                # Format standard deviation with warning for high variance
                def format_stddev(stddev):
                    if stddev is None:
                        return "   -  "
                    elif stddev > 50:  # High variance warning
                        return "{:5.1f}⚠".format(stddev)
                    else:
                        return "{:5.1f} ".format(stddev)
                
                print(" 🟢 {:<7} {:>7.3f}   {:>3.0f}W  {:>4}MHz {:>5.3f}V {:>5.1f}  {:<6} {:>5.2f}  {:>4.0f}  {} {} {}".format(
                    metrics.miner_name,
                    metrics.hashrate_th,
                    metrics.power_w,
                    metrics.frequency_mhz,
                    metrics.core_voltage_set_v,
                    metrics.efficiency_jth,
                    eff_display,
                    metrics.temperature_c,
                    metrics.fan_speed_rpm,
                    format_stddev(metrics.hashrate_stddev_60s),
                    format_stddev(metrics.hashrate_stddev_300s),
                    format_stddev(metrics.hashrate_stddev_600s)
                ))
                
                total_hashrate_th += metrics.hashrate_th
                total_expected_th += metrics.expected_hashrate_th
                total_power += metrics.power_w
                online_count += 1
            else:
                print(" 🔴 {:<7} OFFLINE".format(metrics.miner_name))
        
        print("-" * 105)
        
        if online_count > 0:
            avg_efficiency_jth = total_power / total_hashrate_th if total_hashrate_th > 0 else 0
            avg_temp = sum(m.temperature_c for m in metrics_list if m.status == 'ONLINE') / online_count
            avg_fan = sum(m.fan_speed_rpm for m in metrics_list if m.status == 'ONLINE') / online_count
            
            if total_expected_th > 0:
                fleet_efficiency = (total_hashrate_th / total_expected_th * 100)
                if fleet_efficiency >= 95:
                    fleet_eff_display = "{:3.0f}🔥".format(fleet_efficiency)
                elif fleet_efficiency >= 85:
                    fleet_eff_display = "{:3.0f}⚡".format(fleet_efficiency)
                else:
                    fleet_eff_display = "{:3.0f}%".format(fleet_efficiency)
            else:
                fleet_eff_display = "N/A"
            
            print(" 📊 TOTALS   {:>7.3f}   {:>3.0f}W    ---   ---   {:>5.1f}  {:<6} {:>5.2f}  {:>4.0f}".format(
                total_hashrate_th,
                total_power,
                avg_efficiency_jth,
                fleet_eff_display,
                avg_temp,
                avg_fan
            ))
        else:
            print(" ❌ ALL OFF")
        
        print("=" * 105)
        print()
        
        # Additional info including variance details
        if online_count > 0:
            print("📊 Additional Info:")
            for metrics in metrics_list:
                if metrics.status == 'ONLINE':
                    variance_info = ""
                    if metrics.hashrate_stddev_60s is not None and metrics.hashrate_stddev_60s > 30:
                        variance_info = " ⚠️ High variance!"
                    
                    print("   {}: VR:{:.1f}°C  ActV:{:.3f}V  InV:{:.2f}V  Pool:{}{}".format(
                        metrics.miner_name,
                        metrics.vr_temperature_c,
                        metrics.core_voltage_actual_v, 
                        metrics.input_voltage_v,
                        metrics.pool_url.split('/')[-1] if metrics.pool_url else 'N/A',
                        variance_info
                    ))
            print()
        
        # Show legend
        print("💡 Legend: σ = Standard Deviation (GH/s) | 60s/300s/600s windows")
        print("   ⚠️ = High variance warning (σ > 50 GH/s)")
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
            
            # Variance information
            print("\n📊 Hashrate Variance:")
            if metrics.hashrate_variance_60s is not None:
                print("   60s:  σ²={:.2f}, σ={:.2f} GH/s".format(
                    metrics.hashrate_variance_60s, metrics.hashrate_stddev_60s))
            if metrics.hashrate_variance_300s is not None:
                print("   300s: σ²={:.2f}, σ={:.2f} GH/s".format(
                    metrics.hashrate_variance_300s, metrics.hashrate_stddev_300s))
            if metrics.hashrate_variance_600s is not None:
                print("   600s: σ²={:.2f}, σ={:.2f} GH/s".format(
                    metrics.hashrate_variance_600s, metrics.hashrate_stddev_600s))
            
            print("\n🔌 Power:           {:.1f} W".format(metrics.power_w))
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

# HTML template for web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Bitaxe Monitor</title>
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
            margin-bottom: 10px;
        }
        .update-time {
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 20px;
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
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
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
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }
        .metric-row:last-child {
            border-bottom: none;
        }
        .metric-label {
            color: #7f8c8d;
        }
        .metric-value {
            font-weight: 500;
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
        .variance-warning {
            color: #e74c3c;
        }
        .chart-container {
            margin-top: 15px;
            height: 150px;
            position: relative;
        }
        canvas {
            width: 100% !important;
            height: 100% !important;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #7f8c8d;
            font-size: 12px;
        }
        @media (max-width: 768px) {
            .miners-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>🔥 Bitaxe Monitor</h1>
        <div class="update-time" id="updateTime">Loading...</div>
        
        <div class="stats-grid" id="statsGrid">
            <!-- Summary stats will be inserted here -->
        </div>
        
        <div class="miners-grid" id="minersGrid">
            <!-- Miner cards will be inserted here -->
        </div>
        
        <div class="footer">
            Auto-refreshes every 5 seconds | <span id="csvFile">CSV: </span>
        </div>
    </div>

    <script>
        const charts = {};
        
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
        
        function createMinerChart(canvasId, minerName) {
            const ctx = document.getElementById(canvasId).getContext('2d');
            
            charts[minerName] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Hashrate (GH/s)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                        }
                    },
                    scales: {
                        x: {
                            display: false
                        },
                        y: {
                            beginAtZero: false,
                            ticks: {
                                font: {
                                    size: 10
                                }
                            }
                        }
                    }
                }
            });
        }
        
        function updateChart(minerName, historyData) {
            if (!charts[minerName] || !historyData || historyData.length === 0) return;
            
            const chart = charts[minerName];
            const labels = historyData.map(d => {
                const date = new Date(d.time);
                return date.toLocaleTimeString();
            });
            const data = historyData.map(d => d.hashrate);
            
            chart.data.labels = labels;
            chart.data.datasets[0].data = data;
            chart.update('none');
        }
        
        function updateData() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    // Update timestamp
                    document.getElementById('updateTime').textContent = 
                        'Last updated: ' + new Date(data.timestamp).toLocaleString();
                    
                    // Update CSV filename
                    document.getElementById('csvFile').textContent = 'CSV: ' + data.csv_file;
                    
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
                            <div class="stat-label">Average J/TH</div>
                            <div class="stat-value">${data.avg_efficiency_jth.toFixed(1)} J/TH</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Miners Online</div>
                            <div class="stat-value">${data.online_count}/${data.total_count}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Average Temp</div>
                            <div class="stat-value">${data.avg_temperature.toFixed(1)}°C</div>
                        </div>
                    `;
                    document.getElementById('statsGrid').innerHTML = statsHtml;
                    
                    // Update miner cards
                    let minersHtml = '';
                    data.miners.forEach((miner, index) => {
                        const canvasId = 'chart-' + index;
                        
                        if (miner.status === 'ONLINE') {
                            const varianceWarning = (miner.hashrate_stddev_60s && miner.hashrate_stddev_60s > 50) ? 
                                '<span class="variance-warning"> ⚠️</span>' : '';
                            
                            minersHtml += `
                                <div class="miner-card">
                                    <div class="miner-header">
                                        <div class="miner-name">${miner.miner_name}</div>
                                        <div class="miner-status status-online">ONLINE</div>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Hashrate</span>
                                        <span class="metric-value">${miner.hashrate_th} TH/s${varianceWarning}</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Efficiency</span>
                                        <span class="metric-value ${getEfficiencyClass(miner.hashrate_efficiency_pct)}">${miner.hashrate_efficiency_pct}%</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Power</span>
                                        <span class="metric-value">${miner.power_w} W (${miner.efficiency_jth} J/TH)</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Temperature</span>
                                        <span class="metric-value">${miner.temperature_c}°C / VR: ${miner.vr_temperature_c}°C</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Variance (σ)</span>
                                        <span class="metric-value">
                                            ${miner.hashrate_stddev_60s !== null ? miner.hashrate_stddev_60s + ' GH/s' : '-'} (60s)
                                        </span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Uptime</span>
                                        <span class="metric-value">${miner.uptime_formatted}</span>
                                    </div>
                                    <div class="metric-row">
                                        <span class="metric-label">Shares</span>
                                        <span class="metric-value">✅ ${miner.accepted_shares} / ❌ ${miner.rejected_shares}</span>
                                    </div>
                                    <div class="chart-container">
                                        <canvas id="${canvasId}"></canvas>
                                    </div>
                                </div>
                            `;
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
                    
                    // Initialize or update charts
                    data.miners.forEach((miner, index) => {
                        if (miner.status === 'ONLINE') {
                            const canvasId = 'chart-' + index;
                            if (!charts[miner.miner_name]) {
                                createMinerChart(canvasId, miner.miner_name);
                            }
                            
                            // Fetch and update history data
                            fetch(`/api/history/${miner.miner_name}`)
                                .then(response => response.json())
                                .then(historyData => {
                                    updateChart(miner.miner_name, historyData);
                                });
                        }
                    });
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
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

class WebServer:
    """Flask web server for displaying metrics"""
    
    def __init__(self, collector, csv_filename, host='0.0.0.0', port=8080):
        self.app = Flask(__name__)
        self.collector = collector
        self.csv_filename = csv_filename
        self.host = host
        self.port = port
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string(HTML_TEMPLATE)
        
        @self.app.route('/api/metrics')
        def api_metrics():
            metrics = self.collector.get_latest_metrics()
            
            # Calculate summary statistics
            total_hashrate_th = sum(m.hashrate_th for m in metrics if m.status == 'ONLINE')
            total_expected_th = sum(m.expected_hashrate_th for m in metrics if m.status == 'ONLINE')
            total_power = sum(m.power_w for m in metrics if m.status == 'ONLINE')
            online_count = sum(1 for m in metrics if m.status == 'ONLINE')
            total_count = len(metrics)
            
            fleet_efficiency = 0
            avg_efficiency_jth = 0
            avg_temperature = 0
            
            if online_count > 0:
                if total_expected_th > 0:
                    fleet_efficiency = (total_hashrate_th / total_expected_th) * 100
                if total_hashrate_th > 0:
                    avg_efficiency_jth = total_power / total_hashrate_th
                avg_temperature = sum(m.temperature_c for m in metrics if m.status == 'ONLINE') / online_count
            
            # Prepare response
            response = {
                'timestamp': datetime.now().isoformat(),
                'csv_file': os.path.basename(self.csv_filename),
                'total_hashrate_th': total_hashrate_th,
                'total_expected_th': total_expected_th,
                'total_power_w': total_power,
                'fleet_efficiency': fleet_efficiency,
                'avg_efficiency_jth': avg_efficiency_jth,
                'avg_temperature': avg_temperature,
                'online_count': online_count,
                'total_count': total_count,
                'miners': [m.to_web_dict() for m in metrics]
            }
            
            return jsonify(response)
        
        @self.app.route('/api/history/<miner_name>')
        def api_history(miner_name):
            history_data = self.collector.get_history_data(miner_name, 600)
            return jsonify(history_data)
    
    def run(self):
        """Run the web server in a separate thread"""
        def run_server():
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Get local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print("\n🌐 Web interface available at:")
        print("   - http://localhost:{}".format(self.port))
        print("   - http://{}:{}".format(local_ip, self.port))
        print("   - http://{}:{} (from other devices on LAN)".format(self._get_lan_ip(), self.port))
        print()
    
    def _get_lan_ip(self):
        """Try to get the actual LAN IP address"""
        try:
            # Create a socket to an external host to find the LAN IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return socket.gethostbyname(socket.gethostname())

class MultiBitaxeMonitor:
    """Main monitor class that orchestrates the monitoring process"""
    
    def __init__(self, miners_config, poll_interval=30, expected_hashrates=None, web_port=8080):
        """
        Initialize monitor
        
        Args:
            miners_config: List of miner configurations
            poll_interval: Seconds between polls (default 30)
            expected_hashrates: Optional dict of miner_name -> expected_gh overrides
            web_port: Port for web interface (default 8080)
        """
        self.miners = [MinerConfig(**config) for config in miners_config]
        self.poll_interval = poll_interval
        self.expected_hashrates = expected_hashrates or {}
        self.collector = MetricsCollector(self.expected_hashrates)
        self.logger = DataLogger()
        self.display = Display()
        self.web_server = WebServer(self.collector, self.logger.filename, port=web_port)
    
    def run_monitor(self, show_detailed=False):
        """Main monitoring loop"""
        print("🚀 Starting Multi-Bitaxe Monitor with Variance Tracking and Web Interface")
        print("📊 Monitoring {} miners:".format(len(self.miners)))
        for miner in self.miners:
            print("   - {} ({}:{})".format(miner.name, miner.ip, miner.port))
        print("📁 Data will be saved to: {}".format(self.logger.filename))
        print("🔄 Polling every {} seconds...".format(self.poll_interval))
        print("📈 Tracking hashrate variance over 60s, 300s, and 600s windows")
        
        # Start web server
        self.web_server.run()
        
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
        expected_hashrates=expected_hashrates,
        web_port=8080  # Web interface port
    )
    
    # Set show_detailed=True to see individual miner details
    monitor.run_monitor(show_detailed=False)

if __name__ == "__main__":
    main()