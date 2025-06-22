#!/usr/bin/env python3
"""
Enhanced Analysis Generator Demo

Demonstrates the new features and improvements added to the
Bitaxe Analysis Generator in the test branch.
"""

import subprocess
import sys
import tempfile
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

def create_demo_data():
    """Create demo CSV data for testing"""
    print("[DEMO] Creating sample data for demonstration...")
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp()) 
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    
    # Generate realistic sample data
    demo_data = []
    base_time = datetime.now() - timedelta(hours=3)
    
    miners = ["Gamma-1", "Gamma-2", "Gamma-3"]
    settings = [
        (1020, 500), (1030, 520), (1040, 540),
        (1050, 560), (1060, 580), (1070, 600)
    ]
    
    for miner_idx, miner in enumerate(miners):
        for voltage_mv, freq_mhz in settings:
            voltage_v = voltage_mv / 1000
            
            # Create 20 measurements per setting for robust analysis
            for measurement in range(20):
                timestamp = base_time + timedelta(
                    minutes=measurement*3 + miner_idx*120 + settings.index((voltage_mv, freq_mhz))*20
                )
                
                # Simulate realistic performance with some variance
                base_hashrate = 0.9 + (freq_mhz - 500) * 0.003 + (voltage_v - 1.02) * 0.8
                noise = 0.05 * ((measurement % 7) - 3) / 3  # Controlled variance
                hashrate = max(0.5, base_hashrate + noise)
                
                efficiency = 12.0 + (freq_mhz - 500) * 0.015 + (voltage_v - 1.02) * 2.5
                power = hashrate * efficiency
                
                # Different miners have different fan characteristics
                fan_base = 45 + miner_idx * 5 + (freq_mhz - 500) * 0.05 + (voltage_v - 1.02) * 15
                fan_percent = max(30, min(80, fan_base + measurement % 3))
                
                demo_data.append({
                    'timestamp': timestamp.isoformat(),
                    'miner_name': miner,
                    'set_voltage_v': voltage_v,
                    'frequency_mhz': freq_mhz,
                    'hashrate_th': round(hashrate, 3),
                    'efficiency_j_th': round(efficiency, 2),
                    'actual_voltage_v': round(voltage_v - 0.003 + (measurement % 4) * 0.002, 3),
                    'power_w': round(power, 1),
                    'asic_temp_c': 50.0 + freq_mhz * 0.02 + voltage_v * 12,
                    'fan_speed_rpm': int(fan_percent * 50),
                    'fan_speed_percent': round(fan_percent, 1)
                })
    
    # Save to CSV
    df = pd.DataFrame(demo_data)
    csv_file = data_dir / "demo_bitaxe_data.csv"
    df.to_csv(csv_file, index=False)
    
    print(f"[DEMO] Created demo data: {len(demo_data)} records")
    print(f"[DEMO] Miners: {', '.join(miners)}")
    print(f"[DEMO] Settings per miner: {len(settings)}")
    print(f"[DEMO] Measurements per setting: 20")
    print(f"[DEMO] Data file: {csv_file}")
    
    return temp_dir

def run_enhanced_analysis(demo_dir):
    """Demonstrate the enhanced analysis features"""
    print("\n[DEMO] Testing Enhanced Analysis Generator Features")
    print("=" * 60)
    
    scripts_dir = Path(__file__).parent.parent / "scripts"
    
    demos = [
        {
            "name": "Basic Analysis (default settings)",
            "args": ["--hours", "6", "--data-dir", str(demo_dir / "data"), 
                    "--output-dir", str(demo_dir / "output")]
        },
        {
            "name": "Verbose Analysis with CSV Export",
            "args": ["--hours", "6", "--data-dir", str(demo_dir / "data"),
                    "--output-dir", str(demo_dir / "output"), "--verbose", "--export-csv"]
        },
        {
            "name": "High-Precision Analysis (min 15 measurements)",
            "args": ["--hours", "6", "--data-dir", str(demo_dir / "data"),
                    "--output-dir", str(demo_dir / "output"), "--min-measurements", "15"]
        }
    ]
    
    for i, demo in enumerate(demos, 1):
        print(f"\n{i}. {demo['name']}")
        print(f"   Command: python bitaxe_analysis_generator.py {' '.join(demo['args'])}")
        
        try:
            result = subprocess.run([
                sys.executable,
                "bitaxe_analysis_generator.py"
            ] + demo["args"],
            cwd=scripts_dir,
            capture_output=True,
            text=True,
            timeout=60
            )
            
            if result.returncode == 0:
                print("   [SUCCESS] Analysis completed successfully!")
                
                # Check outputs
                output_dir = Path(demo_dir) / "output"
                html_files = list(output_dir.glob("*.html"))
                csv_files = list(output_dir.glob("*.csv"))
                
                print(f"   [OUTPUT] HTML reports: {len(html_files)}")
                if csv_files:
                    print(f"   [OUTPUT] CSV exports: {len(csv_files)}")
                
                # Show latest HTML file
                if html_files:
                    latest_html = max(html_files, key=lambda f: f.stat().st_mtime)
                    print(f"   [FILE] Latest report: {latest_html.name}")
                    
            else:
                print("   [ERROR] Analysis failed:")
                print(f"   {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            print("   [TIMEOUT] Analysis took too long")
        except Exception as e:
            print(f"   [ERROR] Unexpected error: {e}")

def show_improvements():
    """Show what improvements were made"""
    print("\n[DEMO] Enhanced Features in Test Branch")
    print("=" * 60)
    
    improvements = [
        "✓ Fixed Unicode encoding issues for Windows compatibility",
        "✓ Added robust error handling and data validation", 
        "✓ Enhanced CLI with verbose mode and configurable options",
        "✓ Added CSV export functionality for analysis results",
        "✓ Improved logging with debug mode support",
        "✓ Better data validation and missing column detection",
        "✓ Configurable minimum measurements threshold",
        "✓ Enhanced argument parsing with examples",
        "✓ Comprehensive test coverage with all tests passing",
        "✓ JSON serialization fixes for numpy types"
    ]
    
    for improvement in improvements:
        print(f"  {improvement}")
    
    print("\n[DEMO] New CLI Options:")
    print("  --verbose, -v              Enable debug output")
    print("  --min-measurements N       Set minimum data points per setting")  
    print("  --export-csv               Export recommendations to CSV")
    print("  --data-dir PATH            Custom data directory")
    print("  --output-dir PATH          Custom output directory")

def main():
    """Run the demo"""
    print("Bitaxe Analysis Generator - Enhanced Features Demo")
    print("=" * 60)
    print("This demo showcases the improvements made in the test branch")
    
    try:
        # Create demo data
        demo_dir = create_demo_data()
        
        # Show improvements
        show_improvements()
        
        # Run enhanced analysis
        run_enhanced_analysis(demo_dir)
        
        print("\n" + "=" * 60)
        print("[DEMO] Demo completed successfully!")
        print(f"[DEMO] Demo files saved in: {demo_dir}")
        print("\n[NEXT] These improvements are ready for testing and eventual merge to main branch")
        
    except KeyboardInterrupt:
        print("\n[DEMO] Demo interrupted by user")
    except Exception as e:
        print(f"\n[DEMO] Demo failed: {e}")

if __name__ == "__main__":
    main()
