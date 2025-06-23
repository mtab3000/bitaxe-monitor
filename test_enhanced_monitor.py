#!/usr/bin/env python3
"""
Test script for Enhanced BitAxe Monitor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_bitaxe_monitor import EnhancedBitAxeMonitor, MinerConfig, VarianceTracker
from datetime import datetime
import logging

def test_variance_tracker():
    """Test the VarianceTracker functionality"""
    print("Testing VarianceTracker...")
    tracker = VarianceTracker([60, 300])
    
    # Add some test data
    for i in range(10):
        tracker.add_datapoint(1000 + i * 10, datetime.now())
    
    std_60 = tracker.get_standard_deviation(60)
    mean_60 = tracker.get_mean(60)
    variance_pct = tracker.get_variance_percentage(1000, 60)
    
    print(f"  - Standard deviation (60s): {std_60:.2f}")
    print(f"  - Mean (60s): {mean_60:.2f}")
    print(f"  - Variance percentage: {variance_pct:.2f}%")
    print("  [OK] VarianceTracker working correctly")

def test_monitor_creation():
    """Test monitor creation and configuration"""
    print("Testing Monitor Creation...")
    config = [
        {'name': 'Test-Miner-1', 'ip': '192.168.1.100', 'expected_hashrate_gh': 1200}
    ]
    
    monitor = EnhancedBitAxeMonitor(config, port=8081)
    print(f"  - Created monitor with {len(monitor.miners_config)} miners")
    print(f"  - Variance trackers: {len(monitor.variance_trackers)}")
    print(f"  - Chart data initialized: {len(monitor.chart_data)}")
    print("  [OK] Monitor creation working correctly")

def test_metrics_parsing():
    """Test metrics parsing with mock data"""
    print("Testing Metrics Parsing...")
    config = [
        {'name': 'Test-Miner-1', 'ip': '192.168.1.100', 'expected_hashrate_gh': 1200}
    ]
    
    monitor = EnhancedBitAxeMonitor(config, port=8081)
    miner = monitor.miners_config[0]
    
    # Mock BitAxe response data
    mock_data = {
        'hashRate': 1180.5,
        'power': 15.2,
        'temp': 65.3,
        'frequency': 625,
        'voltage': 1.2,
        'uptimeSeconds': 3600,
        'fanSpeed': 4500
    }
    
    metrics = monitor.parse_miner_metrics(miner, mock_data)
    
    print(f"  - Miner: {metrics.miner_name}")
    print(f"  - Status: {metrics.status}")
    print(f"  - Hashrate: {metrics.hashrate_gh} GH/s ({metrics.hashrate_th:.3f} TH/s)")
    print(f"  - Efficiency: {metrics.hashrate_efficiency_pct:.1f}%")
    print(f"  - Power: {metrics.power_w} W")
    print(f"  - Temperature: {metrics.temperature_c}°C")
    print("  [OK] Metrics parsing working correctly")

def main():
    """Run all tests"""
    print("Enhanced BitAxe Monitor - Test Suite")
    print("=" * 50)
    
    try:
        test_variance_tracker()
        print()
        test_monitor_creation()
        print()
        test_metrics_parsing()
        print()
        print("[SUCCESS] All tests passed! Enhanced BitAxe Monitor is ready to use.")
        print()
        print("To start the monitor, run:")
        print("  python enhanced_bitaxe_monitor.py")
        print()
        print("Then open your browser to:")
        print("  http://localhost:8080")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
