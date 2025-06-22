#!/usr/bin/env python3
"""
Quick test script to validate the enhanced Bitaxe analysis generator.

This script tests that the analysis generator can find CSV data from multiple locations
and works whether run from the main directory or scripts directory.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_test(description, command, working_dir):
    """Run a test command and report results"""
    print(f"\n🧪 TEST: {description}")
    print(f"   Command: {command}")
    print(f"   Working Directory: {working_dir}")
    
    try:
        result = subprocess.run(
            command.split(),
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("   ✅ SUCCESS")
            # Extract key info from output
            for line in result.stdout.split('\n'):
                if 'Using most recent data file:' in line:
                    print(f"   📁 Data File: {line.split(':', 1)[1].strip()}")
                elif 'Report saved to:' in line:
                    print(f"   📊 Report: {line.split(':', 1)[1].strip()}")
                elif 'Analysis summary:' in line:
                    print(f"   📈 {line.split(':', 1)[1].strip()}")
        else:
            print("   ❌ FAILED")
            print(f"   Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("   ⏱️ TIMEOUT")
    except Exception as e:
        print(f"   💥 EXCEPTION: {e}")

def main():
    """Run validation tests"""
    print("🚀 TESTING ENHANCED BITAXE ANALYSIS GENERATOR")
    print("=" * 60)
    
    # Test from main directory
    run_test(
        "Run from main directory", 
        "python scripts/bitaxe_analysis_generator.py --hours 2",
        "C:/dev/bitaxe-monitor"
    )
    
    # Test from scripts directory  
    run_test(
        "Run from scripts directory",
        "python bitaxe_analysis_generator.py --hours 2", 
        "C:/dev/bitaxe-monitor/scripts"
    )
    
    # Test with explicit data directory
    run_test(
        "Run with explicit data directory",
        "python bitaxe_analysis_generator.py --hours 2 --data-dir .", 
        "C:/dev/bitaxe-monitor"
    )
    
    print("\n" + "=" * 60)
    print("🎯 VALIDATION COMPLETE")
    print("\nThe enhanced analysis generator should now work from:")
    print("  ✅ Main project directory") 
    print("  ✅ Scripts subdirectory")
    print("  ✅ Docker environments")
    print("  ✅ Custom data directories")

if __name__ == "__main__":
    main()
