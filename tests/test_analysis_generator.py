#!/usr/bin/env python3
"""
Test for Bitaxe Analysis Generator

Tests basic functionality of the analysis generator
without requiring real data.
"""

import unittest
import tempfile
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add scripts directory to path for testing
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

try:
    from bitaxe_analysis_generator import BitaxeAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False

class TestBitaxeAnalyzer(unittest.TestCase):
    """Test cases for Bitaxe Analysis Generator"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not ANALYZER_AVAILABLE:
            self.skipTest("Analysis generator not available")
            
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.output_dir = Path(self.temp_dir) / "output"
        
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        self.analyzer = BitaxeAnalyzer(str(self.data_dir), str(self.output_dir))
    
    def create_test_data(self) -> Path:
        """Create test CSV data for analysis"""
        # Create sample data with multiple voltage/frequency combinations
        test_data = []
        base_time = datetime.now() - timedelta(hours=2)
        
        miners = ["Gamma-1", "Gamma-2", "Gamma-3"]
        voltages = [1.020, 1.030, 1.040]  # V
        frequencies = [500, 520, 540]     # MHz
        
        for i, miner in enumerate(miners):
            for j, voltage in enumerate(voltages):
                for k, freq in enumerate(frequencies):
                    # Create multiple measurements for each combination
                    for measurement in range(10):
                        timestamp = base_time + timedelta(minutes=measurement*2 + i*30 + j*10 + k*3)
                        
                        # Simulate realistic performance data
                        base_hashrate = 1.0 + (freq - 500) * 0.002 + (voltage - 1.020) * 0.5
                        hashrate_noise = 0.1 * (measurement % 3 - 1)  # Some variance
                        hashrate = base_hashrate + hashrate_noise
                        
                        efficiency = 12.0 + (freq - 500) * 0.01 + (voltage - 1.020) * 2.0
                        power = hashrate * efficiency
                        
                        test_data.append({
                            'timestamp': timestamp.isoformat(),
                            'miner_name': miner,
                            'set_voltage_v': voltage,
                            'frequency_mhz': freq,
                            'hashrate_th': round(hashrate, 3),
                            'efficiency_j_th': round(efficiency, 2),
                            'actual_voltage_v': round(voltage - 0.005 + (measurement % 3) * 0.003, 3),
                            'power_w': round(power, 1),
                            'asic_temp_c': 55.0 + freq * 0.02 + voltage * 10,
                            'fan_speed_rpm': 2000 + freq * 2 + voltage * 500,
                            'fan_speed_percent': 40 + freq * 0.04 + voltage * 8
                        })
        
        # Create CSV file
        df = pd.DataFrame(test_data)
        csv_file = self.data_dir / "test_bitaxe_data.csv"
        df.to_csv(csv_file, index=False)
        
        return csv_file
    
    def test_find_latest_csv(self):
        """Test CSV file discovery"""
        # Should return None when no CSV files exist
        result = self.analyzer.find_latest_csv()
        self.assertIsNone(result)
        
        # Create a test CSV file
        csv_file = self.create_test_data()
        
        # Should find the CSV file
        result = self.analyzer.find_latest_csv()
        self.assertEqual(result, csv_file)
    
    def test_load_and_filter_data(self):
        """Test data loading and filtering"""
        csv_file = self.create_test_data()
        
        # Load all data
        df = self.analyzer.load_and_filter_data(csv_file, hours=24)
        self.assertFalse(df.empty)
        self.assertIn('timestamp', df.columns)
        self.assertIn('miner_name', df.columns)
        
        # Test timestamp filtering
        df_short = self.analyzer.load_and_filter_data(csv_file, hours=1)
        self.assertTrue(len(df_short) < len(df))
    
    def test_analyze_miner_performance(self):
        """Test miner performance analysis"""
        csv_file = self.create_test_data()
        df = self.analyzer.load_and_filter_data(csv_file, hours=24)
        
        # Analyze first miner
        analysis = self.analyzer.analyze_miner_performance(df, "Gamma-1")
        
        self.assertNotIn('error', analysis)
        self.assertEqual(analysis['miner_name'], "Gamma-1")
        self.assertGreater(analysis['total_measurements'], 0)
        self.assertGreater(analysis['unique_settings'], 0)
        
        # Check recommendations structure
        recs = analysis['recommendations']
        for rec_type in ['best_efficiency', 'best_stability', 'best_hashrate', 'best_balanced']:
            self.assertIn(rec_type, recs)
            rec = recs[rec_type]
            self.assertIn('set_voltage_mv', rec)
            self.assertIn('frequency_mhz', rec)
            self.assertIn('hashrate_th', rec)
            self.assertIn('efficiency_j_th', rec)
    
    def test_generate_html_report(self):
        """Test HTML report generation"""
        csv_file = self.create_test_data()
        df = self.analyzer.load_and_filter_data(csv_file, hours=24)
        
        # Analyze all miners
        analyses = []
        for miner in ["Gamma-1", "Gamma-2", "Gamma-3"]:
            analysis = self.analyzer.analyze_miner_performance(df, miner)
            analyses.append(analysis)
        
        # Generate HTML report
        html_content = self.analyzer.generate_html_report(analyses, 24)
        
        # Basic HTML structure checks
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('<title>Bitaxe Performance Analysis', html_content)
        self.assertIn('plotly.js', html_content)
        
        # Check for miner sections
        for miner in ["Gamma-1", "Gamma-2", "Gamma-3"]:
            self.assertIn(miner, html_content)
        
        # Check for recommendation sections
        self.assertIn('EFFICIENCY CHAMPION', html_content)
        self.assertIn('STABILITY CHAMPION', html_content)
        self.assertIn('HASHRATE CHAMPION', html_content)
    
    def test_empty_data_handling(self):
        """Test handling of empty or insufficient data"""
        # Test with empty dataframe
        empty_df = pd.DataFrame()
        analysis = self.analyzer.analyze_miner_performance(empty_df, "Gamma-1")
        self.assertIn('error', analysis)
        
        # Test with non-existent miner
        csv_file = self.create_test_data()
        df = self.analyzer.load_and_filter_data(csv_file, hours=24)
        analysis = self.analyzer.analyze_miner_performance(df, "NonExistent")
        self.assertIn('error', analysis)

class TestAnalysisGeneratorIntegration(unittest.TestCase):
    """Integration tests for the complete analysis workflow"""
    
    @unittest.skipUnless(ANALYZER_AVAILABLE, "Analysis generator not available")
    def test_full_analysis_workflow(self):
        """Test the complete analysis workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data" 
            output_dir = Path(temp_dir) / "output"
            
            data_dir.mkdir()
            output_dir.mkdir()
            
            analyzer = BitaxeAnalyzer(str(data_dir), str(output_dir))
            
            # Create test data
            test_data = []
            base_time = datetime.now() - timedelta(hours=1)
            
            for i in range(50):
                timestamp = base_time + timedelta(minutes=i)
                test_data.append({
                    'timestamp': timestamp.isoformat(),
                    'miner_name': 'Gamma-1',
                    'set_voltage_v': 1.030,
                    'frequency_mhz': 520,
                    'hashrate_th': 1.1 + (i % 10) * 0.01,  # Some variance
                    'efficiency_j_th': 13.5,
                    'actual_voltage_v': 1.025,
                    'power_w': 15.0,
                    'asic_temp_c': 58.0,
                    'fan_speed_rpm': 3000,
                    'fan_speed_percent': 55.0
                })
            
            df = pd.DataFrame(test_data)
            csv_file = data_dir / "test_data.csv"
            df.to_csv(csv_file, index=False)
            
            # Run analysis
            try:
                analyzer.run_analysis(hours=2)
                
                # Check if HTML file was created
                html_files = list(output_dir.glob("*.html"))
                self.assertGreater(len(html_files), 0, "No HTML report generated")
                
                # Check HTML content
                html_file = html_files[0]
                content = html_file.read_text(encoding='utf-8')
                self.assertIn('Gamma-1', content)
                self.assertIn('plotly.js', content)
                
            except Exception as e:
                self.fail(f"Full workflow failed: {e}")

def run_tests():
    """Run all tests"""
    print("Testing Bitaxe Analysis Generator")
    print("=" * 50)
    
    if not ANALYZER_AVAILABLE:
        print("ERROR: Analysis generator not available for testing")
        print("   Make sure pandas and numpy are installed")
        return False
    
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBitaxeAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysisGeneratorIntegration))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("SUCCESS: All tests passed!")
        return True
    else:
        print(f"FAILED: {len(result.failures)} test(s) failed")
        print(f"ERROR: {len(result.errors)} error(s) occurred")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
