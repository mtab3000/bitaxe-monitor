#!/usr/bin/env python3
"""
Local Pylint Runner

Runs pylint checks on the entire codebase with the same configuration
as the GitHub Actions workflow. Use this before committing code to
ensure it passes CI/CD quality checks.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"[SUCCESS] {description}")
            return True
        else:
            print(f"[FAILED] {description} (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"[ERROR] {description} - {e}")
        return False

def check_pylint_installation():
    """Check if pylint is installed"""
    try:
        import pylint
        print(f"[OK] Pylint is installed (version: {pylint.__version__})")
        return True
    except ImportError:
        print("[ERROR] Pylint is not installed")
        print("Install with: pip install pylint")
        return False

def main():
    """Main execution"""
    print("BITAXE MONITOR - LOCAL PYLINT RUNNER")
    print("="*60)
    
    # Check if we're in the right directory
    if not Path('.pylintrc').exists():
        print("[ERROR] .pylintrc not found. Please run from project root directory.")
        sys.exit(1)
    
    # Check pylint installation
    if not check_pylint_installation():
        sys.exit(1)
    
    # Install requirements if needed
    print("\nInstalling requirements...")
    run_command("pip install -r requirements.txt", "Installing requirements")
    
    # Define checks to run
    checks = [
        {
            "cmd": "pylint src/ --rcfile=.pylintrc --output-format=text --reports=yes --score=yes",
            "description": "Pylint check on source code (src/)",
            "critical": True
        },
        {
            "cmd": "pylint scripts/ --rcfile=.pylintrc --output-format=text --reports=yes --score=yes",
            "description": "Pylint check on scripts (scripts/)",
            "critical": True
        },
        {
            "cmd": "pylint tests/ --rcfile=.pylintrc --output-format=text --reports=yes --score=yes --disable=W0212,R0201",
            "description": "Pylint check on tests (tests/)",
            "critical": False
        },
        {
            "cmd": "pylint examples/ --rcfile=.pylintrc --output-format=text --reports=yes --score=yes",
            "description": "Pylint check on examples (examples/)",
            "critical": False
        }
    ]
    
    # Run all checks
    results = []
    critical_failures = 0
    
    for check in checks:
        success = run_command(check["cmd"], check["description"])
        results.append({
            "description": check["description"],
            "success": success,
            "critical": check["critical"]
        })
        
        if not success and check["critical"]:
            critical_failures += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("PYLINT RESULTS SUMMARY")
    print(f"{'='*60}")
    
    for result in results:
        status = "[PASS]" if result["success"] else "[FAIL]"
        critical = " (CRITICAL)" if result["critical"] else ""
        print(f"{status} {result['description']}{critical}")
    
    print(f"\nCritical failures: {critical_failures}")
    
    if critical_failures == 0:
        print("\n[SUCCESS] ALL CRITICAL CHECKS PASSED!")
        print("Your code is ready for commit/push.")
        exit_code = 0
    else:
        print(f"\n[WARNING] {critical_failures} CRITICAL CHECKS FAILED")
        print("Please fix the issues before committing.")
        exit_code = 1
    
    # Additional recommendations
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    print("• Fix any critical pylint issues before committing")
    print("• Consider fixing non-critical issues for better code quality")
    print("• Run this script regularly during development")
    print("• Use 'black .' to auto-format code before pylint")
    print("• Check the .pylintrc file for disabled warnings")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
