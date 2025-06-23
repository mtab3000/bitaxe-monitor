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
- Multiple chart types: hashrate, efficiency, variance, voltage
- Background alerts for low efficiency
- Persistent charts that never disappear

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
from flask import Flask, render_template_string, jsonify, request
import socket
from variance_persistence import VarianceTracker

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
        # Store tuples of (timestamp, hashrate_gh, efficiency_pct, voltage_v, expected_hashrate_gh) for each miner
        self.history = defaultdict(deque)
        self.max_history_seconds = 600  # Keep 10 minutes of history
    
    def add_sample(self, miner_name, timestamp, hashrate_gh, efficiency_pct=0, voltage_v=0, expected_hashrate_gh=0):
        """Add a sample for a miner with expected hashrate for variance baseline"""
        history = self.history[miner_name]
        
        # Convert timestamp string to datetime if needed
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # Add new sample with additional metrics including expected hashrate
        history.append((timestamp, hashrate_gh, efficiency_pct, voltage_v, expected_hashrate_gh))
        
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
        for timestamp, hashrate, _, _, _ in history:
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
    
    def calculate_directional_variance(self, miner_name, window_seconds):
        """Calculate positive and negative variance relative to expected hashrate"""
        history = self.history.get(miner_name, deque())
        if not history:
            return {"positive_variance": None, "negative_variance": None, "avg_deviation": None}
        
        # Get current time and calculate cutoff
        current_time = history[-1][0]
        cutoff_time = current_time - timedelta(seconds=window_seconds)
        
        # Collect samples within the window with their expected values
        deviations = []
        positive_deviations = []
        negative_deviations = []
        
        for timestamp, hashrate, _, _, expected_hashrate in history:
            if timestamp >= cutoff_time and expected_hashrate > 0:
                deviation = hashrate - expected_hashrate
                deviations.append(deviation)
                
                if deviation >= 0:
                    positive_deviations.append(deviation)
                else:
                    negative_deviations.append(abs(deviation))
        
        # Need at least 2 samples for meaningful calculations
        if len(deviations) < 2:
            return {"positive_variance": None, "negative_variance": None, "avg_deviation": None}
        
        try:
            # Calculate average deviation
            avg_deviation = sum(deviations) / len(deviations)
            
            # Calculate positive variance (standard deviation of positive deviations)
            positive_variance = None
            if len(positive_deviations) > 1:
                pos_mean = sum(positive_deviations) / len(positive_deviations)
                pos_var = sum((x - pos_mean) ** 2 for x in positive_deviations) / (len(positive_deviations) - 1)
                positive_variance = pos_var ** 0.5
            
            # Calculate negative variance (standard deviation of negative deviations)
            negative_variance = None
            if len(negative_deviations) > 1:
                neg_mean = sum(negative_deviations) / len(negative_deviations)
                neg_var = sum((x - neg_mean) ** 2 for x in negative_deviations) / (len(negative_deviations) - 1)
                negative_variance = neg_var ** 0.5
            
            return {
                "positive_variance": positive_variance,
                "negative_variance": negative_variance, 
                "avg_deviation": avg_deviation,
                "positive_count": len(positive_deviations),
                "negative_count": len(negative_deviations),
                "total_samples": len(deviations)
            }
        except:
            return {"positive_variance": None, "negative_variance": None, "avg_deviation": None}
    
    def get_sample_count(self, miner_name, window_seconds):
        """Get number of samples in specified window"""
        history = self.history.get(miner_name, deque())
        if not history:
            return 0
        
        current_time = history[-1][0]
        cutoff_time = current_time - timedelta(seconds=window_seconds)
        
        count = sum(1 for timestamp, _, _, _, _ in history if timestamp >= cutoff_time)
        return count
    
    def get_history_data(self, miner_name, window_seconds=600):
        """Get historical data for charting"""
        history = self.history.get(miner_name, deque())
        if not history:
            return []
        
        current_time = history[-1][0]
        cutoff_time = current_time - timedelta(seconds=window_seconds)
        
        data = []
        for timestamp, hashrate, efficiency, voltage, expected_hashrate in history:
            if timestamp >= cutoff_time:
                data.append({
                    'time': timestamp.isoformat(),
                    'hashrate': hashrate,
                    'efficiency': efficiency,
                    'voltage': voltage,
                    'expected_hashrate': expected_hashrate,
                    'deviation': hashrate - expected_hashrate if expected_hashrate > 0 else 0
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
        
        # Directional variance metrics (new - positive/negative deviation tracking)
        self.hashrate_positive_variance_60s = kwargs.get('hashrate_positive_variance_60s', None)
        self.hashrate_positive_variance_300s = kwargs.get('hashrate_positive_variance_300s', None)
        self.hashrate_positive_variance_600s = kwargs.get('hashrate_positive_variance_600s', None)
        self.hashrate_negative_variance_60s = kwargs.get('hashrate_negative_variance_60s', None)
        self.hashrate_negative_variance_300s = kwargs.get('hashrate_negative_variance_300s', None)
        self.hashrate_negative_variance_600s = kwargs.get('hashrate_negative_variance_600s', None)
        self.hashrate_avg_deviation_60s = kwargs.get('hashrate_avg_deviation_60s', None)
        self.hashrate_avg_deviation_300s = kwargs.get('hashrate_avg_deviation_300s', None)
        self.hashrate_avg_deviation_600s = kwargs.get('hashrate_avg_deviation_600s', None)
        
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
            'hashrate_positive_variance_60s': self.hashrate_positive_variance_60s if self.hashrate_positive_variance_60s is not None else '',
            'hashrate_positive_variance_300s': self.hashrate_positive_variance_300s if self.hashrate_positive_variance_300s is not None else '',
            'hashrate_positive_variance_600s': self.hashrate_positive_variance_600s if self.hashrate_positive_variance_600s is not None else '',
            'hashrate_negative_variance_60s': self.hashrate_negative_variance_60s if self.hashrate_negative_variance_60s is not None else '',
            'hashrate_negative_variance_300s': self.hashrate_negative_variance_300s if self.hashrate_negative_variance_300s is not None else '',
            'hashrate_negative_variance_600s': self.hashrate_negative_variance_600s if self.hashrate_negative_variance_600s is not None else '',
            'hashrate_avg_deviation_60s': self.hashrate_avg_deviation_60s if self.hashrate_avg_deviation_60s is not None else '',
            'hashrate_avg_deviation_300s': self.hashrate_avg_deviation_300s if self.hashrate_avg_deviation_300s is not None else '',
            'hashrate_avg_deviation_600s': self.hashrate_avg_deviation_600s if self.hashrate_avg_deviation_600s is not None else '',
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
            'hashrate_positive_variance_60s', 'hashrate_positive_variance_300s', 'hashrate_positive_variance_600s',
            'hashrate_negative_variance_60s', 'hashrate_negative_variance_300s', 'hashrate_negative_variance_600s',
            'hashrate_avg_deviation_60s', 'hashrate_avg_deviation_300s', 'hashrate_avg_deviation_600s',
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
    
    def __init__(self, expected_hashrates=None, data_dir="data"):
        """
        Initialize collector
        
        Args:
            expected_hashrates: Optional dict of miner_name -> expected_gh overrides
            data_dir: Directory for enhanced variance data storage
        """
        self.api = BitaxeAPI()
        self.expected_hashrates = expected_hashrates or {}
        self.hashrate_history = HashrateHistory()
        self.latest_metrics = []  # Store latest metrics for web display
        self.metrics_lock = threading.Lock()
        
        # Enhanced variance tracking
        self.variance_tracker = VarianceTracker(data_dir)
    
    def collect_miner_metrics(self, miner_config):
        """Collect comprehensive metrics from a single miner"""
        timestamp = datetime.now()
        timestamp_str = timestamp.isoformat()
        
        # Get system data
        system_data = self.api.get_system_info(miner_config)
        
        if not system_data:
            return self._create_offline_metrics(miner_config, timestamp_str)
        
        metrics = self._parse_system_data(miner_config, timestamp_str, system_data)
        
        # Add sample to history and calculate variance
        if metrics.status == 'ONLINE':
            self.hashrate_history.add_sample(
                miner_config.name, 
                timestamp, 
                metrics.hashrate_gh,
                metrics.hashrate_efficiency_pct,
                metrics.core_voltage_actual_v,
                metrics.expected_hashrate_gh  # Add expected hashrate for baseline variance
            )
            
            # Calculate variance for different windows
            metrics.hashrate_variance_60s = self.hashrate_history.calculate_variance(miner_config.name, 60)
            metrics.hashrate_variance_300s = self.hashrate_history.calculate_variance(miner_config.name, 300)
            metrics.hashrate_variance_600s = self.hashrate_history.calculate_variance(miner_config.name, 600)
            
            # Calculate standard deviation
            metrics.hashrate_stddev_60s = self.hashrate_history.calculate_std_dev(miner_config.name, 60)
            metrics.hashrate_stddev_300s = self.hashrate_history.calculate_std_dev(miner_config.name, 300)
            metrics.hashrate_stddev_600s = self.hashrate_history.calculate_std_dev(miner_config.name, 600)
            
            # Calculate directional variance (positive/negative relative to expected hashrate)
            variance_data = {}
            for window_seconds, suffix in [(60, '60s'), (300, '300s'), (600, '600s')]:
                directional_var = self.hashrate_history.calculate_directional_variance(miner_config.name, window_seconds)
                setattr(metrics, f'hashrate_positive_variance_{suffix}', directional_var.get('positive_variance'))
                setattr(metrics, f'hashrate_negative_variance_{suffix}', directional_var.get('negative_variance'))
                setattr(metrics, f'hashrate_avg_deviation_{suffix}', directional_var.get('avg_deviation'))
                
                # Store variance data for enhanced logging
                variance_data[suffix] = directional_var
            
            # Enhanced variance tracking and persistence
            try:
                self.variance_tracker.log_miner_variance(
                    timestamp, miner_config.name,
                    variance_data.get('60s', {}),
                    variance_data.get('300s', {}), 
                    variance_data.get('600s', {}),
                    metrics.expected_hashrate_gh,
                    metrics.hashrate_gh
                )
            except Exception as e:
                logger.warning(f"Failed to log enhanced variance data for {miner_config.name}: {e}")
        
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
            # Check for Docker environment variable
            data_file = os.getenv('DATA_FILE')
            if data_file:
                filename = data_file
            else:
                filename = "bitaxe_monitor_data.csv"  # Fixed filename - always append to same file
        
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
        print("\n>> Multi-Bitaxe Summary - {}".format(timestamp))
        print("=" * 140)
        
        # Enhanced table with voltage/frequency info and all variance windows
        print(" Miner     Hash(TH)  Power  FREQ    SET V   ACT V   J/TH  Eff%   Temp   Fan    s60s   s300s  s600s  Variance  Uptime")
        print("-" * 140)
        
        total_hashrate_th = 0
        total_expected_th = 0
        total_power = 0
        online_count = 0
        
        for metrics in metrics_list:
            if metrics.status == 'ONLINE':
                # Format efficiency with ASCII symbols
                if metrics.expected_hashrate_gh > 0:
                    eff_pct = metrics.hashrate_efficiency_pct
                    if eff_pct >= 95:
                        eff_display = "{:3.0f}!".format(eff_pct)  # Excellent
                    elif eff_pct >= 85:
                        eff_display = "{:3.0f}*".format(eff_pct)  # Good
                    elif eff_pct < 70:
                        eff_display = "{:3.0f}!".format(eff_pct)  # Warning
                    else:
                        eff_display = "{:3.0f}%".format(eff_pct)
                else:
                    eff_display = "N/A"
                
                # Format standard deviation with warning for high variance
                def format_stddev(stddev):
                    if stddev is None:
                        return "   -  "
                    elif stddev > 50:  # High variance warning
                        return "{:5.1f}!".format(stddev)
                    else:
                        return "{:5.1f} ".format(stddev)
                
                # Format variance rating
                variance_rating = ""
                if metrics.hashrate_stddev_60s is not None:
                    if metrics.hashrate_stddev_60s < 20:
                        variance_rating = "STABLE"
                    elif metrics.hashrate_stddev_60s < 40:
                        variance_rating = "MEDIUM"
                    else:
                        variance_rating = "HIGH!"
                else:
                    variance_rating = "  -   "
                
                print(" ON  {:<7} {:>7.3f}   {:>3.0f}W  {:>4}MHz {:>5.3f}V {:>5.3f}V {:>5.1f}  {:<6} {:>5.2f}  {:>4.0f}  {} {} {}  {:<6} {}".format(
                    metrics.miner_name,
                    metrics.hashrate_th,
                    metrics.power_w,
                    metrics.frequency_mhz,
                    metrics.core_voltage_set_v,
                    metrics.core_voltage_actual_v,
                    metrics.efficiency_jth,
                    eff_display,
                    metrics.temperature_c,
                    metrics.fan_speed_rpm,
                    format_stddev(metrics.hashrate_stddev_60s),
                    format_stddev(metrics.hashrate_stddev_300s),
                    format_stddev(metrics.hashrate_stddev_600s),
                    variance_rating,
                    metrics._format_uptime()
                ))
                
                total_hashrate_th += metrics.hashrate_th
                total_expected_th += metrics.expected_hashrate_th
                total_power += metrics.power_w
                online_count += 1
            else:
                print(" OFF {:<7} OFFLINE".format(metrics.miner_name))
        
        print("-" * 140)
        
        if online_count > 0:
            avg_efficiency_jth = total_power / total_hashrate_th if total_hashrate_th > 0 else 0
            avg_temp = sum(m.temperature_c for m in metrics_list if m.status == 'ONLINE') / online_count
            avg_fan = sum(m.fan_speed_rpm for m in metrics_list if m.status == 'ONLINE') / online_count
            
            if total_expected_th > 0:
                fleet_efficiency = (total_hashrate_th / total_expected_th * 100)
                if fleet_efficiency >= 95:
                    fleet_eff_display = "{:3.0f}!".format(fleet_efficiency)
                elif fleet_efficiency >= 85:
                    fleet_eff_display = "{:3.0f}*".format(fleet_efficiency)
                else:
                    fleet_eff_display = "{:3.0f}%".format(fleet_efficiency)
            else:
                fleet_eff_display = "N/A"
            
            print(" SUM TOTALS   {:>7.3f}   {:>3.0f}W    ---     ---     ---   {:>5.1f}  {:<6} {:>5.2f}  {:>4.0f}".format(
                total_hashrate_th,
                total_power,
                avg_efficiency_jth,
                fleet_eff_display,
                avg_temp,
                avg_fan
            ))
        else:
            print(" ALL MINERS OFFLINE")
        
        print("=" * 140)
        print()
        
        # Additional info including variance details
        if online_count > 0:
            print(">> Additional Info:")
            for metrics in metrics_list:
                if metrics.status == 'ONLINE':
                    variance_info = ""
                    if metrics.hashrate_stddev_60s is not None and metrics.hashrate_stddev_60s > 30:
                        variance_info = " [HIGH VARIANCE!]"
                    
                    print("   {}: VR:{:.1f}C  InputV:{:.2f}V  Pool:{}{}".format(
                        metrics.miner_name,
                        metrics.vr_temperature_c,
                        metrics.input_voltage_v,
                        metrics.pool_url.split('/')[-1] if metrics.pool_url else 'N/A',
                        variance_info
                    ))
            print()
        
        # Show legend
        print(">> Legend: s = Standard Deviation (GH/s) | 60s/300s/600s windows | SET V = Set Voltage | ACT V = Actual Voltage")
        print("   ! = High value/warning | * = Good performance | STABLE/MEDIUM/HIGH = Variance rating")
        print()
    
    @staticmethod
    def show_detailed(metrics_list):
        """Display detailed metrics for each online miner"""
        for metrics in metrics_list:
            if metrics.status != 'ONLINE':
                continue
            
            print("\n>> {} ({}) - {}".format(
                metrics.miner_name, metrics.miner_ip, metrics.timestamp[:19]))
            print("=" * 60)
            print("Hashrate:        {:.2f} GH/s ({:.3f} TH/s)".format(
                metrics.hashrate_gh, metrics.hashrate_th))
            if metrics.expected_hashrate_gh > 0:
                print("Expected:        {:.2f} GH/s ({:.3f} TH/s) - {:.1f}% efficiency".format(
                    metrics.expected_hashrate_gh, metrics.expected_hashrate_th, metrics.hashrate_efficiency_pct))
            
            # Variance information
            print("\nHashrate Variance:")
            if metrics.hashrate_variance_60s is not None:
                print("   60s:  s²={:.2f}, s={:.2f} GH/s".format(
                    metrics.hashrate_variance_60s, metrics.hashrate_stddev_60s))
            if metrics.hashrate_variance_300s is not None:
                print("   300s: s²={:.2f}, s={:.2f} GH/s".format(
                    metrics.hashrate_variance_300s, metrics.hashrate_stddev_300s))
            if metrics.hashrate_variance_600s is not None:
                print("   600s: s²={:.2f}, s={:.2f} GH/s".format(
                    metrics.hashrate_variance_600s, metrics.hashrate_stddev_600s))
            
            print("\nPower:           {:.1f} W".format(metrics.power_w))
            print("Efficiency:      {:.1f} J/TH".format(metrics.efficiency_jth))
            print("Temperature:     {:.1f}C (ASIC) / {:.1f}C (VR)".format(
                metrics.temperature_c, metrics.vr_temperature_c))
            print("Fan Speed:       {} RPM".format(metrics.fan_speed_rpm))
            print("Core Voltage:    {:.3f}V (Set) / {:.3f}V (Actual)".format(
                metrics.core_voltage_set_v, metrics.core_voltage_actual_v))
            print("Input Voltage:   {:.2f}V".format(metrics.input_voltage_v))
            print("Frequency:       {} MHz".format(metrics.frequency_mhz))
            print("Best Diff:       {:,}".format(metrics.best_diff))
            print("Session Diff:    {:,}".format(metrics.session_diff))
            print("Accepted:        {}".format(metrics.accepted_shares))
            print("Rejected:        {}".format(metrics.rejected_shares))
            print("Uptime:          {:,} seconds ({})".format(metrics.uptime_s, metrics._format_uptime()))
            print("WiFi RSSI:       {} dBm".format(metrics.wifi_rssi))
            print("Pool:            {}".format(metrics.pool_url))
            print("Worker:          {}".format(metrics.worker_name))
            print("ASIC Model:      {}".format(metrics.asic_model))
            print("Board Version:   {}".format(metrics.board_version))
            print("Firmware:        {}".format(metrics.firmware_version))

# Enhanced HTML template with stacked charts and mobile/desktop toggle
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Bitaxe Monitor - Enhanced Persistent</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
            transition: background-color 0.5s ease;
        }
        body.efficiency-alert {
            background: #ffebee !important;
            animation: pulse-red 2s infinite;
        }
        @keyframes pulse-red {
            0% { background-color: #ffebee; }
            50% { background-color: #ffcdd2; }
            100% { background-color: #ffebee; }
        }
        .container {
            max-width: 1800px;
            margin: 0 auto;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 5px;
            text-align: center;
        }
        .view-controls {
            text-align: center;
            margin-bottom: 15px;
        }
        .view-toggle {
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin: 0 10px;
        }
        .view-toggle.active {
            background: #28a745;
        }
        .view-toggle:hover {
            opacity: 0.9;
        }
        .update-time {
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 20px;
            text-align: center;
        }
        .alert-banner {
            background: #f44336;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
            display: none;
        }
        .alert-banner.show {
            display: block;
        }
        
        /* Desktop View */
        .desktop-view .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .desktop-view .miners-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            gap: 20px;
        }
        .desktop-view .chart-container {
            height: 200px;
            margin-bottom: 15px;
        }
        
        /* Mobile View */
        .mobile-view .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }
        .mobile-view .miners-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
        }
        .mobile-view .chart-container {
            height: 150px;
            margin-bottom: 10px;
        }
        .mobile-view .stat-card {
            padding: 10px;
        }
        .mobile-view .stat-value {
            font-size: 18px;
        }
        .mobile-view .miner-card {
            padding: 15px;
        }
        .mobile-view .metric-row {
            padding: 4px 0;
            font-size: 12px;
        }
        .mobile-view .voltage-info {
            padding: 8px;
            margin-top: 8px;
        }
        .mobile-view .voltage-row {
            font-size: 11px;
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
        .variance-warning {
            color: #e74c3c;
        }
        .chart-container {
            position: relative;
            background: white;
            border: 1px solid #ecf0f1;
            border-radius: 8px;
            padding: 10px;
        }
        .chart-title {
            font-size: 12px;
            font-weight: bold;
            color: #666;
            margin-bottom: 5px;
            text-align: center;
        }
        canvas {
            width: 100% !important;
            height: 100% !important;
        }
        .voltage-info {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            border-left: 4px solid #007bff;
        }
        .voltage-row {
            display: flex;
            justify-content: space-between;
            margin: 4px 0;
            font-size: 12px;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #7f8c8d;
            font-size: 12px;
        }
        @media (max-width: 768px) {
            .desktop-view .miners-grid {
                grid-template-columns: 1fr;
            }
            body {
                padding: 10px;
            }
        }
        
        /* Enhanced Variance Analytics Styles */
        .variance-controls {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
            gap: 10px;
        }
        
        .variance-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .variance-btn.active {
            background: #007bff;
        }
        
        .variance-btn:hover {
            opacity: 0.9;
        }
        
        .variance-summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .variance-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #007bff;
        }
        
        .variance-card.warning {
            border-left-color: #ffc107;
        }
        
        .variance-card.danger {
            border-left-color: #dc3545;
        }
        
        .variance-card.success {
            border-left-color: #28a745;
        }
        
        .variance-metric {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 4px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .variance-metric:last-child {
            border-bottom: none;
        }
        
        .variance-label {
            font-weight: 500;
            color: #666;
        }
        
        .variance-value {
            font-weight: bold;
        }
        
        .variance-value.good {
            color: #28a745;
        }
        
        .variance-value.warning {
            color: #ffc107;
        }
        
        .variance-value.danger {
            color: #dc3545;
        }
        
        .report-controls {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .report-controls select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .report-display {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            min-height: 300px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 12px;
        }
        
        @media (max-width: 768px) {
            .variance-summary-grid {
                grid-template-columns: 1fr;
            }
            .report-controls {
                flex-direction: column;
                align-items: stretch;
            }
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="desktop-view">
    <div class="container">
        <h1>Bitaxe Monitor - Enhanced Persistent</h1>
        
        <div class="view-controls">
            <button class="view-toggle active" onclick="switchView('desktop')">Desktop View</button>
            <button class="view-toggle" onclick="switchView('mobile')">Mobile View</button>
        </div>
        
        <div class="update-time" id="updateTime">Loading...</div>
        
        <div class="alert-banner" id="alertBanner">
            [!] EFFICIENCY ALERT: One or more miners below 80% efficiency!
        </div>
        
        <div class="stats-grid" id="statsGrid">
            <!-- Summary stats will be inserted here -->
        </div>
        
        <div class="miners-grid" id="minersGrid">
            <!-- Miner cards will be inserted here -->
        </div>
        
        <!-- Enhanced Variance Analytics Dashboard -->
        <div id="varianceAnalytics" style="display: none; margin-top: 30px;">
            <h2>Enhanced Variance Analytics</h2>
            
            <div class="variance-controls">
                <button onclick="toggleVarianceView('analytics')" class="variance-btn active" id="analyticsBtn">Analytics</button>
                <button onclick="toggleVarianceView('reports')" class="variance-btn" id="reportsBtn">Reports</button>
            </div>
            
            <!-- Analytics View -->
            <div id="analyticsView" class="variance-view">
                <div class="variance-summary-grid" id="varianceSummaryGrid">
                    <!-- Summary cards will be inserted here -->
                </div>
            </div>
            
            <!-- Reports View -->
            <div id="reportsView" class="variance-view" style="display: none;">
                <div class="report-controls">
                    <select id="reportMinerSelect">
                        <option value="">Select Miner</option>
                    </select>
                    <select id="reportDaysSelect">
                        <option value="7">7 Days</option>
                        <option value="14">14 Days</option>
                        <option value="30" selected>30 Days</option>
                    </select>
                    <button onclick="generateVarianceReport()" class="variance-btn">Generate Report</button>
                </div>
                <div id="reportDisplay" class="report-display">
                    <p>Select a miner and click "Generate Report" to view detailed variance analysis.</p>
                </div>
            </div>
        </div>
        
        <!-- Toggle button for variance analytics -->
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="toggleVarianceAnalytics()" class="view-toggle" id="varianceToggle">
                Show Enhanced Variance Analytics
            </button>
        </div>
        
        <div class="footer">
            Auto-refreshes every 5 seconds | <span id="csvFile">CSV: </span>
        </div>
    </div>

    <script>
        const charts = {};
        let minersInitialized = false;
        let lastMinerCount = 0;
        let currentView = 'desktop';
        
        function switchView(view) {
            const body = document.body;
            const buttons = document.querySelectorAll('.view-toggle');
            
            // Update body class
            body.className = body.className.replace(/desktop-view|mobile-view/g, '');
            body.classList.add(view + '-view');
            
            // Update active button
            buttons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.textContent.toLowerCase().includes(view)) {
                    btn.classList.add('active');
                }
            });
            
            currentView = view;
            
            // Trigger chart resize after view change
            setTimeout(() => {
                Object.values(charts).forEach(chart => {
                    if (chart && chart.resize) {
                        chart.resize();
                    }
                });
            }, 100);
        }
        
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
        
        function createMinerChart(canvasId, minerName, chartType) {
            const ctx = document.getElementById(canvasId);
            if (!ctx) {
                console.log('Canvas not found:', canvasId);
                return;
            }
            
            let config = {
                type: 'line',
                data: {
                    labels: [],
                    datasets: []
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
                            display: true,
                            ticks: {
                                font: { size: 9 },
                                maxTicksLimit: 4
                            }
                        },
                        y: {
                            beginAtZero: false,
                            ticks: {
                                font: { size: 9 }
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    elements: {
                        point: {
                            radius: 1
                        }
                    },
                    animation: {
                        duration: 0  // Disable animations for better performance
                    }
                }
            };
            
            // Configure chart based on type
            switch(chartType) {
                case 'hashrate':
                    config.data.datasets = [{
                        label: 'Hashrate (GH/s)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1,
                        fill: true
                    }];
                    break;
                case 'efficiency':
                    config.data.datasets = [{
                        label: 'Efficiency (%)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.1,
                        fill: true
                    }];
                    config.options.scales.y.beginAtZero = false;
                    config.options.scales.y.suggestedMin = 50;
                    config.options.scales.y.suggestedMax = 110;
                    break;
                case 'variance':
                    config.data.datasets = [{
                        label: 'Std Dev (GH/s)',
                        data: [],
                        borderColor: 'rgb(153, 102, 255)',
                        backgroundColor: 'rgba(153, 102, 255, 0.1)',
                        tension: 0.1,
                        fill: true
                    }];
                    config.options.scales.y.beginAtZero = true;
                    config.options.scales.y.title = { display: true, text: 'Standard Deviation (GH/s)' };
                    break;
                case 'directional_variance':
                    config.data.datasets = [
                        {
                            label: 'Expected Hashrate',
                            data: [],
                            borderColor: 'rgb(128, 128, 128)',
                            backgroundColor: 'rgba(128, 128, 128, 0.1)',
                            borderDash: [5, 5],
                            fill: false,
                            pointRadius: 0
                        },
                        {
                            label: 'Actual Hashrate',
                            data: [],
                            borderColor: 'rgb(54, 162, 235)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            fill: false
                        },
                        {
                            label: 'Positive Deviation Zone',
                            data: [],
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            fill: '+1'  // Fill above expected hashrate
                        },
                        {
                            label: 'Negative Deviation Zone',
                            data: [],
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            fill: '+1'  // Fill below expected hashrate
                        }
                    ];
                    config.options.scales.y.beginAtZero = false;
                    config.options.scales.y.title = { display: true, text: 'Hashrate (GH/s)' };
                    break;
                case 'voltage':
                    config.data.datasets = [{
                        label: 'Voltage (V)',
                        data: [],
                        borderColor: 'rgb(255, 159, 64)',
                        backgroundColor: 'rgba(255, 159, 64, 0.1)',
                        tension: 0.1,
                        fill: true
                    }];
                    config.options.scales.y.beginAtZero = false;
                    break;
            }
            
            const chartKey = `${minerName}_${chartType}`;
            charts[chartKey] = new Chart(ctx.getContext('2d'), config);
        }
        
        function calculateVariance(data) {
            if (data.length < 2) return [];
            
            const windowSize = 5; // Calculate variance over 5-point windows
            const variances = [];
            
            for (let i = windowSize - 1; i < data.length; i++) {
                const window = data.slice(i - windowSize + 1, i + 1);
                const mean = window.reduce((a, b) => a + b, 0) / window.length;
                const variance = window.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / window.length;
                variances.push(Math.sqrt(variance)); // Standard deviation
            }
            
            return variances;
        }
        
        function updateChart(minerName, historyData, chartType) {
            const chartKey = `${minerName}_${chartType}`;
            if (!charts[chartKey]) return;
            
            if (historyData && historyData.length > 0) {
                const chart = charts[chartKey];
                const labels = historyData.map(d => {
                    const date = new Date(d.time);
                    return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                });
                
                let data = [];
                switch(chartType) {
                    case 'hashrate':
                        data = historyData.map(d => d.hashrate);
                        break;
                    case 'efficiency':
                        data = historyData.map(d => d.efficiency);
                        break;
                    case 'variance':
                        const hashrateData = historyData.map(d => d.hashrate);
                        const varianceData = calculateVariance(hashrateData);
                        data = new Array(hashrateData.length - varianceData.length).fill(null).concat(varianceData);
                        break;
                    case 'directional_variance':
                        // Create datasets for directional variance visualization
                        const times = historyData.map(d => d.time);
                        const expectedData = historyData.map(d => d.expected_hashrate);
                        const actualData = historyData.map(d => d.hashrate);
                        
                        // Update all four datasets for the directional variance chart
                        charts[chartKey].data.datasets[0].data = expectedData;  // Expected baseline
                        charts[chartKey].data.datasets[1].data = actualData;    // Actual hashrate
                        charts[chartKey].data.datasets[2].data = actualData.map((val, i) => val > expectedData[i] ? val : null);  // Positive deviation
                        charts[chartKey].data.datasets[3].data = actualData.map((val, i) => val < expectedData[i] ? val : null);  // Negative deviation
                        
                        charts[chartKey].data.labels = times;
                        charts[chartKey].update('none');
                        return; // Skip normal data update since we handled it above
                    case 'voltage':
                        data = historyData.map(d => d.voltage);
                        break;
                }
                
                chart.data.labels = labels;
                chart.data.datasets[0].data = data;
                chart.update('none');
            }
        }
        
        function updateMinerData(miner) {
            const minerCard = document.querySelector(`[data-miner="${miner.miner_name}"]`);
            if (!minerCard) return;
            
            // Update metric values only
            const metrics = [
                { selector: '[data-metric="hashrate"]', value: `${miner.hashrate_th} TH/s${(miner.hashrate_stddev_60s && miner.hashrate_stddev_60s > 50) ? ' <span class="variance-warning">[!]</span>' : ''}` },
                { selector: '[data-metric="efficiency"]', value: `${miner.hashrate_efficiency_pct}%`, class: getEfficiencyClass(miner.hashrate_efficiency_pct) },
                { selector: '[data-metric="power"]', value: `${miner.power_w} W (${miner.efficiency_jth} J/TH)` },
                { selector: '[data-metric="temperature"]', value: `${miner.temperature_c}C / VR: ${miner.vr_temperature_c}C` },
                { selector: '[data-metric="frequency"]', value: `${miner.frequency_mhz} MHz` },
                { selector: '[data-metric="uptime"]', value: miner.uptime_formatted },
                { selector: '[data-metric="shares"]', value: `[+] ${miner.accepted_shares} / [-] ${miner.rejected_shares}` },
                { selector: '[data-metric="set_voltage"]', value: `${miner.core_voltage_set_v}V` },
                { selector: '[data-metric="actual_voltage"]', value: `${miner.core_voltage_actual_v}V` },
                { selector: '[data-metric="input_voltage"]', value: `${miner.input_voltage_v}V` },
                { selector: '[data-metric="frequency_detail"]', value: `${miner.frequency_mhz} MHz` },
            ];
            
            metrics.forEach(metric => {
                const element = minerCard.querySelector(metric.selector);
                if (element) {
                    element.innerHTML = metric.value;
                    if (metric.class) {
                        element.className = `metric-value ${metric.class}`;
                    }
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
                            <div class="metric-row">
                                <span class="metric-label">Hashrate</span>
                                <span class="metric-value" data-metric="hashrate"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Efficiency</span>
                                <span class="metric-value" data-metric="efficiency"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Power</span>
                                <span class="metric-value" data-metric="power"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Temperature</span>
                                <span class="metric-value" data-metric="temperature"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Frequency</span>
                                <span class="metric-value" data-metric="frequency"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Uptime</span>
                                <span class="metric-value" data-metric="uptime"></span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Shares</span>
                                <span class="metric-value" data-metric="shares"></span>
                            </div>
                            
                            <div class="voltage-info">
                                <div class="voltage-row">
                                    <span><strong>Voltage/Frequency Settings:</strong></span>
                                </div>
                                <div class="voltage-row">
                                    <span>Set Voltage:</span>
                                    <span data-metric="set_voltage"></span>
                                </div>
                                <div class="voltage-row">
                                    <span>Actual Voltage:</span>
                                    <span data-metric="actual_voltage"></span>
                                </div>
                                <div class="voltage-row">
                                    <span>Input Voltage:</span>
                                    <span data-metric="input_voltage"></span>
                                </div>
                                <div class="voltage-row">
                                    <span>Frequency:</span>
                                    <span data-metric="frequency_detail"></span>
                                </div>
                            </div>
                            
                            <div class="chart-container">
                                <div class="chart-title">Hashrate (GH/s)</div>
                                <canvas id="chart-${index}-hashrate"></canvas>
                            </div>
                            
                            <div class="chart-container">
                                <div class="chart-title">Efficiency (%)</div>
                                <canvas id="chart-${index}-efficiency"></canvas>
                            </div>
                            
                            <div class="chart-container">
                                <div class="chart-title">Variance (σ GH/s)</div>
                                <canvas id="chart-${index}-variance"></canvas>
                            </div>
                            
                            <div class="chart-container">
                                <div class="chart-title">Directional Variance (vs Expected)</div>
                                <canvas id="chart-${index}-directional_variance"></canvas>
                            </div>
                            
                            <div class="chart-container">
                                <div class="chart-title">Voltage (V)</div>
                                <canvas id="chart-${index}-voltage"></canvas>
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
            
            // Initialize charts for online miners
            miners.forEach((miner, index) => {
                if (miner.status === 'ONLINE') {
                    // Create charts for each type
                    ['hashrate', 'efficiency', 'variance', 'directional_variance', 'voltage'].forEach(chartType => {
                        const canvasId = `chart-${index}-${chartType}`;
                        setTimeout(() => createMinerChart(canvasId, miner.miner_name, chartType), 100);
                    });
                }
            });
            
            minersInitialized = true;
        }
        
        function updateData() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    // Check for efficiency alerts
                    const lowEfficiencyMiners = data.miners.filter(m => 
                        m.status === 'ONLINE' && m.hashrate_efficiency_pct < 80
                    );
                    
                    const alertBanner = document.getElementById('alertBanner');
                    const body = document.body;
                    
                    if (lowEfficiencyMiners.length > 0) {
                        alertBanner.classList.add('show');
                        body.classList.add('efficiency-alert');
                        alertBanner.innerHTML = `[!] EFFICIENCY ALERT: ${lowEfficiencyMiners.map(m => m.miner_name).join(', ')} below 80% efficiency!`;
                    } else {
                        alertBanner.classList.remove('show');
                        body.classList.remove('efficiency-alert');
                    }
                    
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
                            <div class="stat-value">${data.avg_temperature.toFixed(1)}C</div>
                        </div>
                    `;
                    document.getElementById('statsGrid').innerHTML = statsHtml;
                    
                    // Initialize miners on first run or if miner count changed
                    if (!minersInitialized || data.miners.length !== lastMinerCount) {
                        initializeMiners(data.miners);
                        lastMinerCount = data.miners.length;
                    } else {
                        // Update existing miners
                        data.miners.forEach(miner => {
                            if (miner.status === 'ONLINE') {
                                updateMinerData(miner);
                            }
                        });
                    }
                    
                    // Update charts with history data
                    data.miners.forEach(miner => {
                        if (miner.status === 'ONLINE') {
                            fetch(`/api/history/${miner.miner_name}`)
                                .then(response => response.json())
                                .then(historyData => {
                                    ['hashrate', 'efficiency', 'variance', 'directional_variance', 'voltage'].forEach(chartType => {
                                        updateChart(miner.miner_name, historyData, chartType);
                                    });
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
        
        // Enhanced Variance Analytics Functions
        let varianceAnalyticsVisible = false;
        let currentVarianceView = 'analytics';
        
        function toggleVarianceAnalytics() {
            const analyticsDiv = document.getElementById('varianceAnalytics');
            const toggleBtn = document.getElementById('varianceToggle');
            
            varianceAnalyticsVisible = !varianceAnalyticsVisible;
            
            if (varianceAnalyticsVisible) {
                analyticsDiv.style.display = 'block';
                toggleBtn.textContent = 'Hide Enhanced Variance Analytics';
                loadVarianceData();
            } else {
                analyticsDiv.style.display = 'none';
                toggleBtn.textContent = 'Show Enhanced Variance Analytics';
            }
        }
        
        function toggleVarianceView(view) {
            // Hide all views
            document.querySelectorAll('.variance-view').forEach(v => v.style.display = 'none');
            document.querySelectorAll('.variance-btn').forEach(b => b.classList.remove('active'));
            
            // Show selected view
            document.getElementById(view + 'View').style.display = 'block';
            document.getElementById(view + 'Btn').classList.add('active');
            
            currentVarianceView = view;
            
            if (view === 'analytics') {
                loadVarianceData();
            } else if (view === 'reports') {
                populateReportMinerSelect();
            }
        }
        
        function loadVarianceData() {
            fetch('/api/variance/summary')
                .then(response => response.json())
                .then(data => {
                    displayVarianceSummary(data.miner_summaries);
                })
                .catch(error => {
                    console.error('Error loading variance data:', error);
                });
        }
        
        function displayVarianceSummary(summaries) {
            const grid = document.getElementById('varianceSummaryGrid');
            let html = '';
            
            for (const [minerName, data] of Object.entries(summaries)) {
                let cardClass = 'variance-card';
                if (data.stability_score >= 80) cardClass += ' success';
                else if (data.stability_score >= 60) cardClass += ' warning';
                else cardClass += ' danger';
                
                html += `
                    <div class="${cardClass}">
                        <h4>${minerName}</h4>
                        <div class="variance-metric">
                            <span class="variance-label">Stability Score:</span>
                            <span class="variance-value ${getStabilityClass(data.stability_score)}">${data.stability_score}/100</span>
                        </div>
                        <div class="variance-metric">
                            <span class="variance-label">Efficiency:</span>
                            <span class="variance-value ${getEfficiencyClass(data.efficiency_pct)}">${data.efficiency_pct}%</span>
                        </div>
                        <div class="variance-metric">
                            <span class="variance-label">Current Deviation:</span>
                            <span class="variance-value">${data.current_deviation > 0 ? '+' : ''}${data.current_deviation} GH/s</span>
                        </div>
                        <div class="variance-metric">
                            <span class="variance-label">Variance (60s):</span>
                            <span class="variance-value">${data.variance_60s} GH/s</span>
                        </div>
                        <div class="variance-metric">
                            <span class="variance-label">Variance (300s):</span>
                            <span class="variance-value">${data.variance_300s} GH/s</span>
                        </div>
                        <div class="variance-metric">
                            <span class="variance-label">Variance (600s):</span>
                            <span class="variance-value">${data.variance_600s} GH/s</span>
                        </div>
                    </div>
                `;
            }
            
            grid.innerHTML = html;
        }
        
        function getStabilityClass(score) {
            if (score >= 80) return 'good';
            if (score >= 60) return 'warning';
            return 'danger';
        }
        
        function populateReportMinerSelect() {
            const select = document.getElementById('reportMinerSelect');
            
            // Get current miners from the main data
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    select.innerHTML = '<option value="">Select Miner</option>';
                    data.miners.forEach(miner => {
                        if (miner.status === 'ONLINE') {
                            select.innerHTML += `<option value="${miner.miner_name}">${miner.miner_name}</option>`;
                        }
                    });
                });
        }
        
        function generateVarianceReport() {
            const minerSelect = document.getElementById('reportMinerSelect');
            const daysSelect = document.getElementById('reportDaysSelect');
            const reportDisplay = document.getElementById('reportDisplay');
            
            const minerName = minerSelect.value;
            const days = daysSelect.value;
            
            if (!minerName) {
                alert('Please select a miner');
                return;
            }
            
            reportDisplay.innerHTML = 'Generating report...';
            
            fetch(`/api/variance/analytics/${minerName}?days=${days}`)
                .then(response => response.json())
                .then(data => {
                    displayVarianceReport(data);
                })
                .catch(error => {
                    reportDisplay.innerHTML = 'Error generating report: ' + error;
                });
        }
        
        function displayVarianceReport(data) {
            const reportDisplay = document.getElementById('reportDisplay');
            
            let report = `Variance Analysis Report for ${data.miner_name}\n`;
            report += `Analysis Period: ${data.analysis_period_days} days\n`;
            report += `Generated: ${new Date().toLocaleString()}\n`;
            report += '='.repeat(60) + '\n\n';
            
            report += 'Variance Trends by Time Window:\n';
            if (data.variance_trends) {
                data.variance_trends.forEach(trend => {
                    report += `  ${trend.window_seconds}s window:\n`;
                    report += `    Average Positive Variance: ${trend.avg_pos_var ? trend.avg_pos_var.toFixed(2) + ' GH/s' : 'N/A'}\n`;
                    report += `    Average Negative Variance: ${trend.avg_neg_var ? trend.avg_neg_var.toFixed(2) + ' GH/s' : 'N/A'}\n`;
                    report += `    Average Stability Score: ${trend.avg_stability ? trend.avg_stability.toFixed(1) + '/100' : 'N/A'}\n`;
                    report += `    Sample Count: ${trend.sample_count}\n\n`;
                });
            }
            
            if (data.worst_stability_periods && data.worst_stability_periods.length > 0) {
                report += 'Worst Stability Periods:\n';
                report += '  Timestamp           | Window | Score | Deviation\n';
                data.worst_stability_periods.slice(0, 5).forEach(period => {
                    const timestamp = new Date(period.timestamp).toLocaleString();
                    report += `  ${timestamp} | ${period.window_seconds.toString().padStart(3)}s   | ${period.stability_score.toFixed(1).padStart(5)} | ${period.deviation_gh >= 0 ? '+' : ''}${period.deviation_gh.toFixed(1)} GH/s\n`;
                });
            }
            
            reportDisplay.innerHTML = report;
        }
        
        // Update every 5 seconds
        setInterval(updateData, 5000);
    </script>
</body>
</html>
'''

class WebServer:
    """Flask web server for displaying metrics"""
    
    def __init__(self, collector, csv_filename, host='0.0.0.0', port=8080):
        """
        Initialize the WebServer with a metrics collector, CSV filename, host, and port.
        
        Sets up the Flask application and configures API and dashboard routes for serving miner metrics and web interface.
        """
        self.app = Flask(__name__)
        self.collector = collector
        self.csv_filename = csv_filename
        self.host = host
        self.port = port
        self.setup_routes()
    
    def setup_routes(self):
        """
        Defines all Flask routes for the web server, including:
        
        - The main dashboard page.
        - API endpoints for retrieving current metrics, historical data, enhanced variance analytics, variance reports, and variance summaries.
        - A debug page for testing API endpoints.
        
        Each route serves either HTML content or JSON data to support the web interface and external integrations.
        """
        @self.app.route('/')
        def index():
            """
            Serves the main dashboard page using the embedded HTML template.
            """
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
        
        @self.app.route('/api/debug/<miner_name>')
        def api_debug(miner_name):
            """Debug endpoint to see raw history data"""
            history_data = self.collector.get_history_data(miner_name, 600)
            if history_data:
                efficiency_values = [d['efficiency'] for d in history_data]
                return jsonify({
                    'miner': miner_name,
                    'data_points': len(history_data),
                    'efficiency_values': efficiency_values,
                    'efficiency_range': {
                        'min': min(efficiency_values) if efficiency_values else 0,
                        'max': max(efficiency_values) if efficiency_values else 0,
                        'avg': sum(efficiency_values) / len(efficiency_values) if efficiency_values else 0
                    },
                    'sample_data': history_data[:5]  # First 5 data points
                })
            return jsonify({'error': 'No data found'})
        
        @self.app.route('/api/variance/analytics/<miner_name>')
        def api_variance_analytics(miner_name):
            """Get enhanced variance analytics for a miner"""
            days = int(request.args.get('days', 7))
            try:
                analytics = self.collector.variance_tracker.get_miner_analytics(miner_name, days)
                return jsonify(analytics)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/variance/report/<miner_name>')
        def api_variance_report(miner_name):
            """Generate and return a variance report for a miner"""
            days = int(request.args.get('days', 30))
            try:
                report_path = self.collector.variance_tracker.export_miner_report(miner_name, days)
                # Return the report path for download
                return jsonify({
                    'report_generated': True,
                    'report_path': report_path,
                    'miner_name': miner_name,
                    'analysis_days': days
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/variance/summary')
        def api_variance_summary():
            """
            Return a JSON summary of variance and stability metrics for all online miners.
            
            The response includes, for each miner, a calculated stability score, efficiency percentage, current deviation from expected hashrate, and variance values (standard deviation) over 60s, 300s, and 600s time windows. The JSON object contains a timestamp and a dictionary of miner summaries keyed by miner name.
            """
            try:
                metrics = self.collector.get_latest_metrics()
                summary = {}
                
                for miner in metrics:
                    if miner.status == 'ONLINE':
                        # Calculate combined stability score across all windows
                        stability_scores = []
                        for window in ['60s', '300s', '600s']:
                            pos_var = getattr(miner, f'hashrate_positive_variance_{window}', None)
                            neg_var = getattr(miner, f'hashrate_negative_variance_{window}', None)
                            avg_dev = getattr(miner, f'hashrate_avg_deviation_{window}', 0)
                            
                            if pos_var is not None and neg_var is not None and miner.expected_hashrate_gh > 0:
                                # Simple stability calculation
                                deviation_pct = abs(avg_dev) / miner.expected_hashrate_gh * 100
                                score = max(0, 100 - deviation_pct * 2)
                                stability_scores.append(score)
                        
                        avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0
                        
                        summary[miner.miner_name] = {
                            'stability_score': round(avg_stability, 1),
                            'efficiency_pct': round(miner.hashrate_efficiency_pct, 1),
                            'current_deviation': round(miner.hashrate_gh - miner.expected_hashrate_gh, 1),
                            'variance_60s': round(getattr(miner, 'hashrate_stddev_60s', 0) or 0, 1),
                            'variance_300s': round(getattr(miner, 'hashrate_stddev_300s', 0) or 0, 1),
                            'variance_600s': round(getattr(miner, 'hashrate_stddev_600s', 0) or 0, 1)
                        }
                
                return jsonify({
                    'timestamp': datetime.now().isoformat(),
                    'miner_summaries': summary
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/debug')
        def debug_page():
            """
            Serves a debug web page for testing API endpoints, displaying the contents of 'debug_web.html' if available, or a fallback page that fetches and displays API metrics from '/api/metrics'.
            """
            try:
                with open('debug_web.html', 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return '''
                <h1>Debug Page</h1>
                <p>Testing API endpoints...</p>
                <script>
                fetch('/api/metrics')
                    .then(response => response.json())
                    .then(data => {
                        document.body.innerHTML += '<h2>API Working!</h2><pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    })
                    .catch(error => {
                        document.body.innerHTML += '<h2>API Error: ' + error + '</h2>';
                    });
                </script>
                '''
    
    def run(self):
        """
        Starts the Flask web server in a background thread and prints local and LAN URLs for accessing the web interface.
        """
        def run_server():
            """
            Starts the Flask web server on the specified host and port with threading enabled and debug mode disabled.
            """
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Get local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        print("\n>> Web interface available at:")
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
    
    def __init__(self, miners_config, poll_interval=60, expected_hashrates=None, web_port=8080):
        """
        Initialize monitor
        
        Args:
            miners_config: List of miner configurations
            poll_interval: Seconds between polls (default 60)
            expected_hashrates: Optional dict of miner_name -> expected_gh overrides
            web_port: Port for web interface (default 8080)
        """
        self.miners = [MinerConfig(**config) for config in miners_config]
        self.poll_interval = poll_interval
        self.expected_hashrates = expected_hashrates or {}
        self.collector = MetricsCollector(self.expected_hashrates, data_dir="data")
        self.logger = DataLogger()
        self.display = Display()
        self.web_server = WebServer(self.collector, self.logger.filename, port=web_port)
    
    def run_monitor(self, show_detailed=False):
        """Main monitoring loop"""
        print(">> Starting Enhanced Multi-Bitaxe Monitor with Persistent Charts")
        print(">> Monitoring {} miners:".format(len(self.miners)))
        for miner in self.miners:
            print("   - {} ({}:{})".format(miner.name, miner.ip, miner.port))
        
        # Check if data file exists and show appropriate message
        if os.path.exists(self.logger.filename):
            print(">> Data will be appended to: {} (existing file)".format(self.logger.filename))
        else:
            print(">> Data will be saved to: {} (new file)".format(self.logger.filename))
        
        print(">> Polling every {} seconds... (Changed from 30s to 60s)".format(self.poll_interval))
        print(">> Features: Hashrate, Efficiency, Variance & Voltage charts")
        print(">> Variance tracking: 60s, 300s, 600s windows")
        print(">> Background alerts for efficiency < 80%")
        print(">> Charts are now persistent and won't disappear!")
        print(">> Using persistent data file - no new files created on restart!")
        
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
            print("\n\n>> Monitoring stopped by user")
            print(">> All data is in persistent file: {}".format(self.logger.filename))
        except Exception as e:
            logger.error("Monitoring error: {}".format(e))
            print(">> All data is in persistent file: {}".format(self.logger.filename))

def load_config_from_env():
    """Load configuration from environment variables for Docker deployment"""
    import os
    
    # Get miner configuration from environment
    miner_names = os.getenv('MINER_NAMES', 'Gamma-1,Gamma-2,Gamma-3').split(',')
    miner_ips = os.getenv('MINER_IPS', '192.168.1.45,192.168.1.46,192.168.1.47').split(',')
    miner_ports = os.getenv('MINER_PORTS', '80,80,80').split(',')
    
    # Build miners config
    miners_config = []
    for i, name in enumerate(miner_names):
        config = {
            'name': name.strip(),
            'ip': miner_ips[i].strip() if i < len(miner_ips) else '192.168.1.45'
        }
        if i < len(miner_ports) and miner_ports[i].strip() != '80':
            config['port'] = int(miner_ports[i].strip())
        miners_config.append(config)
    
    # Get expected hashrates if provided
    expected_hashrates = {}
    expected_rates_str = os.getenv('EXPECTED_HASHRATES', '')
    if expected_rates_str:
        try:
            # Format: "Gamma-1:1200,Gamma-2:1150,Gamma-3:1100"
            for pair in expected_rates_str.split(','):
                if ':' in pair:
                    name, rate = pair.split(':', 1)
                    expected_hashrates[name.strip()] = float(rate.strip())
        except Exception as e:
            print(">> Warning: Could not parse EXPECTED_HASHRATES: {}".format(e))
    
    # Get other settings
    poll_interval = int(os.getenv('POLL_INTERVAL', '60'))
    web_port = int(os.getenv('WEB_PORT', '8080'))
    show_detailed = os.getenv('SHOW_DETAILED', 'false').lower() == 'true'
    
    return {
        'miners_config': miners_config,
        'expected_hashrates': expected_hashrates,
        'poll_interval': poll_interval,
        'web_port': web_port,
        'show_detailed': show_detailed
    }

def main():
    """Main entry point"""
    import os
    
    # Check if running in Docker (environment variables present)
    if os.getenv('MINER_NAMES') or os.getenv('MINER_IPS'):
        print(">> Loading configuration from environment variables (Docker mode)")
        config = load_config_from_env()
        miners_config = config['miners_config']
        expected_hashrates = config['expected_hashrates']
        poll_interval = config['poll_interval']
        web_port = config['web_port']
        show_detailed = config['show_detailed']
    else:
        print(">> Using hardcoded configuration (Local mode)")
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
        
        poll_interval = 60  # Changed from 30 to 60 seconds between polls
        web_port = 8080  # Web interface port
        show_detailed = False
    
    # Create and run monitor
    monitor = MultiBitaxeMonitor(
        miners_config=miners_config,
        poll_interval=poll_interval,
        expected_hashrates=expected_hashrates,
        web_port=web_port
    )
    
    # Set show_detailed based on configuration
    monitor.run_monitor(show_detailed=show_detailed)

if __name__ == "__main__":
    main()
