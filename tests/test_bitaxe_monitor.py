"""
Unit tests for Bitaxe Monitor

This module contains basic tests for the Bitaxe monitoring system.
"""

import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from bitaxe_monitor import ASICSpecs, MinerConfig, HashrateHistory
except ImportError:
    # Skip tests if imports fail
    ASICSpecs = None
    MinerConfig = None
    HashrateHistory = None


class TestASICSpecs(unittest.TestCase):
    """Test ASIC specifications and calculations"""
    
    def setUp(self):
        """Set up test fixtures"""
        if ASICSpecs is None:
            self.skipTest("Could not import ASICSpecs")
    
    def test_calculate_expected_hashrate_bm1370(self):
        """Test BM1370 (Gamma) hashrate calculation"""
        # BM1370 at base frequency should give base hashrate
        result = ASICSpecs.calculate_expected_hashrate('BM1370', 600)
        self.assertEqual(result, 1200)
        
        # Test scaling
        result = ASICSpecs.calculate_expected_hashrate('BM1370', 500)
        expected = 1200 * (500 / 600)
        self.assertAlmostEqual(result, expected, places=1)
    
    def test_calculate_expected_hashrate_bm1368(self):
        """Test BM1368 (Supra) hashrate calculation"""
        result = ASICSpecs.calculate_expected_hashrate('BM1368', 650)
        self.assertEqual(result, 700)
    
    def test_calculate_expected_hashrate_invalid(self):
        """Test invalid inputs"""
        result = ASICSpecs.calculate_expected_hashrate('', 600)
        self.assertEqual(result, 0)
        
        result = ASICSpecs.calculate_expected_hashrate('BM1370', 0)
        self.assertEqual(result, 0)


class TestMinerConfig(unittest.TestCase):
    """Test miner configuration"""
    
    def setUp(self):
        """Set up test fixtures"""
        if MinerConfig is None:
            self.skipTest("Could not import MinerConfig")
    
    def test_miner_config_creation(self):
        """Test basic miner config creation"""
        config = MinerConfig('TestMiner', '192.168.1.100')
        self.assertEqual(config.name, 'TestMiner')
        self.assertEqual(config.ip, '192.168.1.100')
        self.assertEqual(config.port, 80)  # Default port
    
    def test_miner_config_custom_port(self):
        """Test miner config with custom port"""
        config = MinerConfig('TestMiner', '192.168.1.100', 8080)
        self.assertEqual(config.port, 8080)


class TestHashrateHistory(unittest.TestCase):
    """Test hashrate history functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if HashrateHistory is None:
            self.skipTest("Could not import HashrateHistory")
        self.history = HashrateHistory()
    
    def test_add_sample(self):
        """Test adding hashrate samples"""
        from datetime import datetime
        
        timestamp = datetime.now()
        self.history.add_sample('TestMiner', timestamp, 1200, 95, 0.4)
        
        # Check that data was added
        data = self.history.get_history_data('TestMiner')
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['hashrate'], 1200)
        self.assertEqual(data[0]['efficiency'], 95)
        self.assertEqual(data[0]['voltage'], 0.4)
    
    def test_variance_calculation(self):
        """Test variance calculation with insufficient data"""
        # With no data, variance should be None
        variance = self.history.calculate_variance('TestMiner', 60)
        self.assertIsNone(variance)
        
        # With one sample, variance should still be None
        from datetime import datetime
        self.history.add_sample('TestMiner', datetime.now(), 1200)
        variance = self.history.calculate_variance('TestMiner', 60)
        self.assertIsNone(variance)


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality that doesn't require API calls"""
    
    def test_imports(self):
        """Test that we can import the main module"""
        try:
            import bitaxe_monitor
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Could not import bitaxe_monitor: {e}")
    
    def test_environment_detection(self):
        """Test environment variable detection"""
        try:
            from bitaxe_monitor import load_config_from_env
            
            # Test with no environment variables
            os.environ.pop('MINER_NAMES', None)
            os.environ.pop('MINER_IPS', None)
            
            config = load_config_from_env()
            self.assertIsInstance(config, dict)
            self.assertIn('miners_config', config)
            self.assertIn('poll_interval', config)
            
        except ImportError:
            self.skipTest("Could not import load_config_from_env")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
