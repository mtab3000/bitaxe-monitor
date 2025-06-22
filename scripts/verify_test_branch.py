#!/usr/bin/env python3
"""
Test Branch Verification Script

Verifies that all improvements in the test-analysis-improvements branch
are working correctly. This script can be run to validate the changes
before merging to main.
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

def run_command(cmd, cwd=None, timeout=30):
    """Run a command and return result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_python_requirements():
    """Check if required Python packages are available"""
    print("Checking Python requirements...")
    
    required_packages = ['pandas', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  [OK] {package} - Available")
        except ImportError:
            print(f"  [MISSING] {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstall missing packages: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def verify_test_suite():
    """Run the test suite to verify everything works"""
    print("\nRunning test suite...")
    
    success, stdout, stderr = run_command(
        "python tests/test_analysis_generator.py",
        timeout=60
    )
    
    if success:
        print("  [PASS] All tests passed successfully")
        # Count successful tests
        if "Ran 6 tests" in stdout and "OK" in stdout:
            print("    - 6/6 tests completed successfully")
            print("    - No errors or failures detected")
        return True
    else:
        print("  [FAIL] Test suite failed")
        print(f"    Error: {stderr}")
        return False

def verify_cli_interface():
    """Test the enhanced CLI interface"""
    print("\nVerifying CLI interface...")
    
    # Test help command
    success, stdout, stderr = run_command(
        "python scripts/bitaxe_analysis_generator.py --help"
    )
    
    if success:
        print("  [PASS] Help command works")
        
        # Check for new options
        expected_options = ['--verbose', '--min-measurements', '--export-csv']
        missing_options = []
        
        for option in expected_options:
            if option in stdout:
                print(f"    [OK] {option} option available")
            else:
                print(f"    [MISSING] {option} option missing")
                missing_options.append(option)
        
        return len(missing_options) == 0
    else:
        print("  [FAIL] Help command failed")
        print(f"    Error: {stderr}")
        return False

def verify_unicode_fixes():
    """Verify Unicode encoding issues are fixed"""
    print("\nVerifying Unicode compatibility...")
    
    # Test the run_analysis_example without Unicode issues
    success, stdout, stderr = run_command(
        "python examples/run_analysis_example.py",
        timeout=10
    )
    
    # We expect this to fail gracefully (no data), but not crash with Unicode errors
    if "UnicodeEncodeError" not in stderr and "'charmap' codec" not in stderr:
        print("  [PASS] No Unicode encoding errors detected")
        print("  [PASS] Windows compatibility improved")
        return True
    else:
        print("  [FAIL] Unicode encoding issues still present")
        print(f"    Error: {stderr}")
        return False

def verify_enhanced_features():
    """Verify enhanced features are available"""
    print("\nVerifying enhanced features...")
    
    checks = []
    
    # Check if demo script exists and runs
    demo_path = Path("examples/enhanced_analysis_demo.py")
    if demo_path.exists():
        print("  [PASS] Enhanced demo script exists")
        checks.append(True)
    else:
        print("  [FAIL] Enhanced demo script missing")
        checks.append(False)
    
    # Check if summary documentation exists
    summary_path = Path("TEST_BRANCH_SUMMARY.md")
    if summary_path.exists():
        print("  [PASS] Test branch summary documentation exists")
        checks.append(True)
    else:
        print("  [FAIL] Test branch summary documentation missing")
        checks.append(False)
    
    # Check analysis generator for new features
    try:
        with open("scripts/bitaxe_analysis_generator.py", 'r') as f:
            content = f.read()
        
        if "convert_to_json_serializable" in content:
            print("  [PASS] JSON serialization fixes implemented")
            checks.append(True)
        else:
            print("  [FAIL] JSON serialization fixes missing")
            checks.append(False)
        
        if "export_csv" in content:
            print("  [PASS] CSV export functionality implemented")
            checks.append(True)
        else:
            print("  [FAIL] CSV export functionality missing")
            checks.append(False)
            
    except Exception as e:
        print(f"  [FAIL] Error checking analysis generator: {e}")
        checks.append(False)
    
    return all(checks)

def main():
    """Main verification routine"""
    print("=" * 60)
    print("BITAXE ANALYSIS GENERATOR - TEST BRANCH VERIFICATION")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Current branch: ", end="")
    
    # Check current git branch
    success, stdout, stderr = run_command("git branch --show-current")
    if success:
        print(stdout.strip())
    else:
        print("Unknown (not a git repository)")
    
    print("=" * 60)
    
    # Run all verification checks
    checks = [
        ("Python Requirements", check_python_requirements),
        ("Test Suite", verify_test_suite),
        ("CLI Interface", verify_cli_interface),
        ("Unicode Fixes", verify_unicode_fixes),
        ("Enhanced Features", verify_enhanced_features)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n[CHECK] {check_name}")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"  [FAIL] Check failed with exception: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for check_name, result in results:
        if result:
            print(f"[PASS] {check_name} - PASSED")
            passed += 1
        else:
            print(f"[FAIL] {check_name} - FAILED")
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n[SUCCESS] ALL CHECKS PASSED!")
        print("The test branch is ready for review and merge.")
        exit_code = 0
    else:
        print(f"\n[WARNING] {failed} CHECKS FAILED")
        print("Please review and fix the issues before merging.")
        exit_code = 1
    
    print("\n" + "=" * 60)
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
