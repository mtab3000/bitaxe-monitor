#!/usr/bin/env python3
"""
Demo Mode Bitaxe Monitor

This script runs the enhanced variance monitoring in demo mode with simulated data.
Perfect for testing the interface without actual bitaxe miners.

Author: mtab3000
License: MIT
"""

import sys
import os
import time
import random
from datetime import datetime, timedelta

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bitaxe_monitor import (
    MinerConfig, MinerMetrics, MetricsCollector, DataLogger, 
    Display, WebServer, MultiBitaxeMonitor, ASICSpecs
)

class DemoMinerAPI:
    """Demo API that simulates bitaxe responses"""
    
    def __init__(self):
        """
        Initialize the DemoMinerAPI with base hashrates for simulated miners and record the start time.
        """
        self.base_hashrates = {
            'Demo-Gamma-1': 1200,
            'Demo-Gamma-2': 1150, 
            'Demo-Gamma-3': 1100
        }
        self.start_time = datetime.now()
    
    def get_system_info(self, miner_config, timeout=5):
        """
        Generate and return a dictionary of simulated miner metrics for a given miner configuration.
        
        The returned data mimics real Bitaxe miner responses, including hashrate, power, temperatures, fan speed, voltages, share statistics, uptime, WiFi signal strength, pool information, ASIC model, board version, and firmware version. Values are randomized within realistic ranges to simulate operational variance.
        
        Parameters:
            miner_config: The configuration object for the simulated miner.
        
        Returns:
            dict: Simulated miner metrics with realistic variance.
        """
        miner_name = miner_config.name
        
        # Simulate some variance in hashrate
        base_hashrate = self.base_hashrates.get(miner_name, 1000)
        variance = random.uniform(-50, 80)  # Realistic variance
        actual_hashrate = max(0, base_hashrate + variance)
        
        # Calculate uptime since start
        uptime_seconds = int((datetime.now() - self.start_time).total_seconds())
        
        # Simulate realistic data
        simulated_data = {
            'hashRate': actual_hashrate,  # GH/s
            'power': random.uniform(13, 16),  # Watts
            'temp': random.uniform(55, 75),  # Celsius
            'vrTemp': random.uniform(60, 80),  # VR temp
            'fanrpm': random.randint(3000, 5000),
            'frequency': random.randint(485, 510),  # MHz
            'coreVoltage': random.randint(980, 1050),  # mV
            'coreVoltageActual': random.randint(970, 1060),  # mV  
            'voltage': random.randint(5000, 5200),  # mV (input voltage)
            'bestNonceDiff': random.randint(100000, 10000000),
            'bestSessionNonceDiff': random.randint(50000, 5000000),
            'sharesAccepted': random.randint(100, 10000),
            'sharesRejected': random.randint(0, 50),
            'uptimeSeconds': uptime_seconds,
            'wifiRSSI': random.randint(-70, -30),  # dBm
            'stratumURL': 'demo.pool.com',
            'stratumUser': f'demo.{miner_name.lower()}',
            'ASICModel': 'BM1370',
            'boardVersion': '601',
            'version': 'v2.8.1'
        }
        
        return simulated_data

class DemoMetricsCollector(MetricsCollector):
    """Demo metrics collector with simulated API"""
    
    def __init__(self, expected_hashrates=None, data_dir="data"):
        """
        Initialize the DemoMetricsCollector with simulated miner data sources.
        
        Overrides the base metrics collector to use the DemoMinerAPI for generating synthetic miner metrics instead of querying real hardware.
        """
        super().__init__(expected_hashrates, data_dir)
        self.api = DemoMinerAPI()  # Use demo API instead of real one

def main():
    """
    Starts the Bitaxe Monitor in demo mode, simulating three miners with realistic variance data for testing enhanced variance monitoring features.
    
    This function initializes simulated miner configurations, sets up demo components including metrics collector, data logger, display, and web server, and enters a loop that periodically collects, displays, and logs simulated metrics. The demo runs until interrupted by the user, providing a full-featured test environment without requiring actual mining hardware.
    """
    print("=" * 80)
    print("BITAXE MONITOR - ENHANCED VARIANCE TRACKING - DEMO MODE")
    print("=" * 80)
    print("This demo mode simulates 3 bitaxe miners with realistic variance data.")
    print("Perfect for testing the enhanced variance monitoring interface!")
    print("=" * 80)
    print()
    
    # Demo configuration - no real IPs needed
    demo_miners_config = [
        {'name': 'Demo-Gamma-1', 'ip': '127.0.0.1'},  # Localhost - won't actually connect
        {'name': 'Demo-Gamma-2', 'ip': '127.0.0.2'},  # Demo IPs
        {'name': 'Demo-Gamma-3', 'ip': '127.0.0.3'}   # Demo IPs
    ]
    
    # Expected hashrates for demo
    demo_expected_hashrates = {
        'Demo-Gamma-1': 1200,
        'Demo-Gamma-2': 1150,
        'Demo-Gamma-3': 1100
    }
    
    print(">> Demo Miners:")
    for miner in demo_miners_config:
        expected = demo_expected_hashrates.get(miner['name'], 'Auto')
        print(f"   - {miner['name']} (Expected: {expected} GH/s)")
    print()
    
    # Create demo monitor components
    demo_collector = DemoMetricsCollector(demo_expected_hashrates, data_dir="demo_data")
    demo_logger = DataLogger("demo_bitaxe_data.csv")
    demo_display = Display()
    demo_web_server = WebServer(demo_collector, demo_logger.filename, port=8080)
    
    print(">> Starting Demo Web Server...")
    demo_web_server.run()
    
    print(">> Demo monitor is now running!")
    print(">> Open your browser to: http://localhost:8080")
    print(">> Click 'Show Enhanced Variance Analytics' to see the new features")
    print(">> Press Ctrl+C to stop")
    print()
    print("=" * 80)
    print("DEMO FEATURES AVAILABLE:")
    print("[SUCCESS] Real-time variance monitoring (simulated data)")
    print("[SUCCESS] Directional variance charts with baseline")
    print("[SUCCESS] Multi-window variance tracking (60s, 300s, 600s)")
    print("[SUCCESS] Enhanced variance analytics dashboard")
    print("[SUCCESS] Stability scoring and variance reports")
    print("[SUCCESS] All new API endpoints")
    print("=" * 80)
    print()
    
    try:
        # Demo monitoring loop
        miners = [MinerConfig(**config) for config in demo_miners_config]
        
        while True:
            start_time = time.time()
            
            # Collect demo metrics
            all_metrics = demo_collector.collect_all_metrics(miners)
            
            # Display demo results
            demo_display.show_summary(all_metrics)
            
            # Log demo data
            demo_logger.log_metrics(all_metrics)
            
            # Sleep for demo interval (shorter for more dynamic data)
            elapsed = time.time() - start_time
            sleep_time = max(0, 10 - elapsed)  # 10 second intervals for demo
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        print("\n\n>> Demo stopped by user")
        print(">> Demo data saved to: demo_bitaxe_data.csv")
        print(">> Enhanced variance data in: demo_data/ directory")
        print(">> Thank you for testing the enhanced variance monitoring!")

if __name__ == "__main__":
    main()
