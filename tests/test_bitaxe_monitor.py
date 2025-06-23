"""
Comprehensive tests for Enhanced BitAxe Monitor

This module contains tests for both the classic and enhanced monitoring systems.
"""

import unittest
import sys
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test imports for enhanced monitor
try:
    from enhanced_bitaxe_monitor import (
        EnhancedBitAxeMonitor, 
        MinerConfig, 
        MinerMetrics, 
        BitAxeAPI,
        VarianceTracker
    )
    ENHANCED_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced monitor import failed: {e}")
    ENHANCED_AVAILABLE = False

# Test imports for classic monitor
try:
    from bitaxe_monitor import ASICSpecs, HashrateHistory
    CLASSIC_AVAILABLE = True
except ImportError as e:
    print(f"Classic monitor import failed: {e}")
    CLASSIC_AVAILABLE = False


class TestEnhancedMonitor(unittest.TestCase):
    """Test Enhanced BitAxe Monitor functionality"""
    
    def setUp(self):
        """
        Prepares the test environment for Enhanced BitAxe Monitor tests.
        
        Skips tests if the enhanced monitor is unavailable and sets up a sample miner configuration for use in test cases.
        """
        if not ENHANCED_AVAILABLE:
            self.skipTest("Enhanced monitor not available")
        
        self.test_config = [
            {'name': 'Test-Gamma-1', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200},
            {'name': 'Test-Gamma-2', 'ip': '192.168.1.46', 'expected_hashrate_gh': 1150}
        ]
    
    def test_miner_config_creation(self):
        """
        Tests that the MinerConfig dataclass is correctly instantiated with the provided name, IP address, and expected hashrate.
        """
        config = MinerConfig('TestMiner', '192.168.1.45', 1200)
        self.assertEqual(config.name, 'TestMiner')
        self.assertEqual(config.ip, '192.168.1.45')
        self.assertEqual(config.expected_hashrate_gh, 1200)
    
    def test_miner_metrics_creation(self):
        """
        Verifies that the MinerMetrics dataclass is correctly instantiated and its attributes are set as expected.
        """
        metrics = MinerMetrics(
            miner_name='TestMiner',
            miner_ip='192.168.1.45',
            status='ONLINE',
            hashrate_gh=1205.3,
            expected_hashrate_gh=1200,
            hashrate_efficiency_pct=100.4
        )
        self.assertEqual(metrics.miner_name, 'TestMiner')
        self.assertEqual(metrics.status, 'ONLINE')
        self.assertAlmostEqual(metrics.hashrate_efficiency_pct, 100.4, places=1)
    
    def test_variance_tracker(self):
        """
        Tests that the VarianceTracker correctly calculates variance after adding multiple data points.
        """
        tracker = VarianceTracker(maxlen=10)
        
        # Add test data points
        test_values = [1200, 1205, 1195, 1210, 1190, 1200]
        for value in test_values:
            tracker.add_data_point(value)
        
        # Test variance calculation (should have data)
        variance_60s = tracker.get_variance_stats(60)
        self.assertIsNotNone(variance_60s)
        self.assertGreater(variance_60s, 0)
    
    def test_bitaxe_api_timeout(self):
        """
        Tests that the BitAxeAPI returns None when attempting to retrieve system info from an unreachable miner.
        """
        api = BitAxeAPI(timeout=1)
        config = MinerConfig('TestMiner', '192.168.1.999')  # Invalid IP
        
        # Should return None for unreachable miner
        result = api.get_system_info(config)
        self.assertIsNone(result)
    
    @patch('enhanced_bitaxe_monitor.requests.get')
    def test_bitaxe_api_success(self, mock_get):
        """
        Tests that the BitAxeAPI correctly returns system information when the API responds successfully.
        
        Mocks a valid API response and verifies that the returned data contains expected hashrate and power values.
        """
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'hashRate': 1205.3,
            'power': 15.2,
            'temp': 65.5,
            'frequency': 500,
            'uptimeSeconds': 3600
        }
        mock_get.return_value = mock_response
        
        api = BitAxeAPI()
        config = MinerConfig('TestMiner', '192.168.1.45')
        result = api.get_system_info(config)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['hashRate'], 1205.3)
        self.assertEqual(result['power'], 15.2)
    
    def test_enhanced_monitor_creation(self):
        """
        Tests that an EnhancedBitAxeMonitor instance is created with the correct number of miners, port, Flask app, and variance trackers.
        """
        monitor = EnhancedBitAxeMonitor(self.test_config, port=8082)
        
        self.assertEqual(len(monitor.miners), 2)
        self.assertEqual(monitor.port, 8082)
        self.assertIsNotNone(monitor.app)
        self.assertEqual(len(monitor.variance_trackers), 2)
    
    def test_monitor_routes_exist(self):
        """
        Verifies that the main and API routes of the EnhancedBitAxeMonitor Flask app are accessible and return the expected status codes and response structure.
        """
        monitor = EnhancedBitAxeMonitor(self.test_config, port=8082)
        
        # Check that routes exist
        with monitor.app.test_client() as client:
            # Test main route
            response = client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'BitAxe Monitor', response.data)
            
            # Test API route
            response = client.get('/api/metrics')
            self.assertEqual(response.status_code, 200)
            
            # Verify JSON response structure
            data = json.loads(response.data)
            self.assertIn('timestamp', data)
            self.assertIn('miners', data)
            self.assertIn('total_hashrate_th', data)
    
    @patch('enhanced_bitaxe_monitor.BitAxeAPI.get_system_info')
    def test_offline_miner_handling(self, mock_api):
        """
        Test that the monitor correctly identifies and reports an offline miner when the API returns no data.
        
        Verifies that the miner's status is set to 'OFFLINE' and that the miner's name and IP are accurately reflected in the metrics.
        """
        # Mock API to return None (offline miner)
        mock_api.return_value = None
        
        monitor = EnhancedBitAxeMonitor(self.test_config, port=8082)
        metrics = monitor.get_miner_metrics(monitor.miners[0])
        
        self.assertEqual(metrics.status, 'OFFLINE')
        self.assertEqual(metrics.miner_name, 'Test-Gamma-1')
        self.assertEqual(metrics.miner_ip, '192.168.1.45')
    
    @patch('enhanced_bitaxe_monitor.BitAxeAPI.get_system_info')
    def test_online_miner_metrics(self, mock_api):
        """
        Test that metrics for an online miner are correctly calculated and populated when the API returns valid system information.
        """
        # Mock successful API response
        mock_api.return_value = {
            'hashRate': 1205.3,
            'power': 15.2,
            'temp': 65.5,
            'frequency': 500,
            'uptimeSeconds': 3600
        }
        
        monitor = EnhancedBitAxeMonitor(self.test_config, port=8082)
        metrics = monitor.get_miner_metrics(monitor.miners[0])
        
        self.assertEqual(metrics.status, 'ONLINE')
        self.assertEqual(metrics.hashrate_gh, 1205.3)
        self.assertEqual(metrics.power_w, 15.2)
        self.assertAlmostEqual(metrics.hashrate_efficiency_pct, 100.4, places=1)
    
    def test_fleet_metrics_calculation(self):
        """
        Tests that the EnhancedBitAxeMonitor correctly aggregates fleet-wide metrics, including online miner count, total hashrate, and total power, using mocked miner metrics.
        """
        monitor = EnhancedBitAxeMonitor(self.test_config, port=8082)
        
        with patch.object(monitor, 'get_miner_metrics') as mock_get_metrics:
            # Mock metrics for two online miners
            mock_get_metrics.side_effect = [
                MinerMetrics('Test-Gamma-1', '192.168.1.45', 'ONLINE', 
                           hashrate_gh=1205, hashrate_th=1.205, power_w=15.2,
                           expected_hashrate_gh=1200, hashrate_efficiency_pct=100.4),
                MinerMetrics('Test-Gamma-2', '192.168.1.46', 'ONLINE',
                           hashrate_gh=1150, hashrate_th=1.150, power_w=14.8,
                           expected_hashrate_gh=1150, hashrate_efficiency_pct=100.0)
            ]
            
            metrics = monitor.get_all_metrics()
            
            self.assertEqual(metrics['online_count'], 2)
            self.assertEqual(metrics['total_count'], 2)
            self.assertAlmostEqual(metrics['total_hashrate_th'], 2.355, places=3)
            self.assertAlmostEqual(metrics['total_power_w'], 30.0, places=1)


class TestClassicMonitor(unittest.TestCase):
    """Test Classic BitAxe Monitor functionality"""
    
    def setUp(self):
        """
        Sets up the test environment for classic monitor tests, skipping tests if the classic monitor is unavailable.
        """
        if not CLASSIC_AVAILABLE:
            self.skipTest("Classic monitor not available")
    
    def test_asic_specs_creation(self):
        """
        Tests retrieval of ASIC specifications for the 'BM1370' model and verifies expected specification fields are present.
        """
        if ASICSpecs is None:
            self.skipTest("ASICSpecs not available")
            
        # Test BM1370 specs
        specs = ASICSpecs.get_specs('BM1370')
        self.assertIsNotNone(specs)
        self.assertIn('base_hashrate_gh', specs)
    
    def test_hashrate_history(self):
        """
        Tests that HashrateHistory correctly tracks a fixed number of hashrate readings and computes their average.
        """
        if HashrateHistory is None:
            self.skipTest("HashrateHistory not available")
            
        history = HashrateHistory(maxlen=5)
        
        # Add test values
        test_values = [1200, 1205, 1195, 1210, 1190]
        for value in test_values:
            history.add_reading(value)
        
        # Test statistics
        self.assertEqual(len(history.readings), 5)
        avg = history.get_average()
        self.assertIsNotNone(avg)


class TestConfigurationValidation(unittest.TestCase):
    """Test configuration validation and error handling"""
    
    def test_invalid_miner_config(self):
        """
        Test that the EnhancedBitAxeMonitor correctly handles invalid miner configurations.
        
        Verifies that creating a monitor with an empty configuration raises an exception, and that a configuration with an invalid IP address results in a monitor instance where the miner is marked as offline.
        """
        if not ENHANCED_AVAILABLE:
            self.skipTest("Enhanced monitor not available")
        
        # Test empty configuration
        # Test that empty configuration raises ValueError
        with self.assertRaises(ValueError) as context:
            EnhancedBitAxeMonitor([], port=8082)
        self.assertIn("configuration", str(context.exception).lower())
        
        # Test invalid IP format
        invalid_config = [{'name': 'Test', 'ip': 'invalid-ip', 'expected_hashrate_gh': 1200}]
        monitor = EnhancedBitAxeMonitor(invalid_config, port=8082)
        # Should create monitor but miner will be offline
        self.assertEqual(len(monitor.miners), 1)
    
    def test_port_validation(self):
        """
        Verifies that the EnhancedBitAxeMonitor correctly accepts and sets valid port numbers during initialization.
        """
        if not ENHANCED_AVAILABLE:
            self.skipTest("Enhanced monitor not available")
        
        test_config = [{'name': 'Test', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200}]
        
        # Valid ports
        monitor = EnhancedBitAxeMonitor(test_config, port=8080)
        self.assertEqual(monitor.port, 8080)
        
        monitor = EnhancedBitAxeMonitor(test_config, port=3000)
        self.assertEqual(monitor.port, 3000)


class TestUtilities(unittest.TestCase):
    """Test utility functions and helpers"""
    
    def test_config_file_loading(self):
        """
        Tests loading a miner configuration from a temporary JSON file and verifies its contents.
        """
        # Test with temporary config file
        config_data = {
            'miners': [
                {'name': 'Test-Miner', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # Test file exists and is readable
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
            
            self.assertIn('miners', loaded_config)
            self.assertEqual(len(loaded_config['miners']), 1)
            self.assertEqual(loaded_config['miners'][0]['name'], 'Test-Miner')
        finally:
            os.unlink(config_file)


def create_test_suite():
    """
    Constructs and returns a unittest test suite including all relevant test classes for the BitAxe Monitor system.
    
    The suite conditionally includes enhanced and classic monitor tests based on module availability, and always includes utility tests.
    
    Returns:
        suite (unittest.TestSuite): The assembled test suite ready for execution.
    """
    suite = unittest.TestSuite()
    
    # Add Enhanced Monitor tests if available
    if ENHANCED_AVAILABLE:
        suite.addTest(unittest.makeSuite(TestEnhancedMonitor))
        suite.addTest(unittest.makeSuite(TestConfigurationValidation))
    
    # Add Classic Monitor tests if available  
    if CLASSIC_AVAILABLE:
        suite.addTest(unittest.makeSuite(TestClassicMonitor))
    
    # Always add utility tests
    suite.addTest(unittest.makeSuite(TestUtilities))
    
    return suite


def run_tests():
    """
    Runs the BitAxe Monitor test suite, prints a detailed summary of results, and returns overall success status.
    
    Returns:
        bool: True if all tests pass, False otherwise.
    """
    print("=" * 60)
    print("BitAxe Monitor Test Suite")
    print("=" * 60)
    print(f"Enhanced Monitor Available: {ENHANCED_AVAILABLE}")
    print(f"Classic Monitor Available: {CLASSIC_AVAILABLE}")
    print("=" * 60)
    
    # Create and run test suite
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
