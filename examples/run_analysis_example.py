#!/usr/bin/env python3
"""
Example usage of the Bitaxe Analysis Generator

This script demonstrates how to use the analysis generator
to create comprehensive performance reports.
"""

import subprocess
import sys
from pathlib import Path

def run_analysis_example():
    """Run example analysis with different time windows"""
    
    print("🚀 Bitaxe Analysis Generator - Example Usage")
    print("=" * 60)
    
    # Change to scripts directory
    scripts_dir = Path(__file__).parent.parent / "scripts"
    
    examples = [
        {
            "name": "Last 6 Hours (Recent Optimization)",
            "hours": 6,
            "description": "Quick analysis of recent settings changes"
        },
        {
            "name": "Last 24 Hours (Daily Performance)",
            "hours": 24, 
            "description": "Standard daily performance analysis"
        },
        {
            "name": "Last 48 Hours (Extended Analysis)", 
            "hours": 48,
            "description": "Comprehensive multi-day analysis"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}")
        print(f"   {example['description']}")
        print(f"   Command: python bitaxe_analysis_generator.py --hours {example['hours']}")
        
        # Ask user if they want to run this example
        response = input(f"   Run this analysis? (y/N): ").strip().lower()
        
        if response in ['y', 'yes']:
            print(f"   🔄 Running analysis for last {example['hours']} hours...")
            
            try:
                # Run the analysis generator
                result = subprocess.run([
                    sys.executable,
                    "bitaxe_analysis_generator.py",
                    "--hours", str(example['hours'])
                ], 
                cwd=scripts_dir,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
                )
                
                if result.returncode == 0:
                    print(f"   ✅ Analysis complete!")
                    print(f"   📄 Report saved to: generated_charts/")
                    
                    # Extract filename from output if possible
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        if 'Report saved to:' in line:
                            print(f"   🔗 {line.strip()}")
                            break
                else:
                    print(f"   ❌ Analysis failed:")
                    print(f"   Error: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("   ⏰ Analysis timed out (>2 minutes)")
            except FileNotFoundError:
                print("   ❌ Analysis generator not found")
                print("   Make sure you're running from the project root directory")
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
        else:
            print("   ⏭️  Skipped")
    
    print("\n" + "=" * 60)
    print("📖 For detailed usage instructions, see:")
    print("   docs/analysis-generator.md")
    print("\n💡 Analysis requires historic monitoring data from CSV files")
    print("   Run the monitor first to collect data for analysis")

if __name__ == "__main__":
    run_analysis_example()
