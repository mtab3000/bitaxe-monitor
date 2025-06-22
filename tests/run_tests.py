#!/usr/bin/env python3
"""
Test runner for Bitaxe Monitor

Runs all tests and generates coverage reports.
"""

import sys
import os
import subprocess

def run_tests():
    """Run all tests with coverage"""
    print("🧪 Running Bitaxe Monitor Tests")
    print("=" * 50)
    
    # Add src to Python path
    src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
    sys.path.insert(0, src_path)
    
    # Run pytest with coverage
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', 
            '-v',
            '--cov=src/',
            '--cov-report=term-missing',
            '--cov-report=html'
        ], check=True)
        
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("⚠️  pytest not found, running unittest instead...")
        return run_unittest()

def run_unittest():
    """Fallback to unittest if pytest not available"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'unittest', 
            'discover', 
            '-s', 'tests',
            '-v'
        ], check=True)
        
        print("\n✅ All tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
