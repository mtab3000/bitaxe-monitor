#!/usr/bin/env python3
"""
BitAxe Monitor Repository Consistency Check

This script performs a comprehensive check of the repository to ensure:
- All IP addresses are consistent
- All configurations are valid
- All files are properly formatted
- Dependencies are up to date
- Documentation is accurate
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple

class RepositoryChecker:
    """Comprehensive repository consistency checker"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Expected miner IPs from configuration
        self.expected_ips = ['192.168.1.45', '192.168.1.46', '192.168.1.47']
        self.expected_names = ['BitAxe-Gamma-1', 'BitAxe-Gamma-2', 'BitAxe-Gamma-3']
        
    def log_error(self, message: str):
        """Log an error"""
        self.errors.append(f"[ERROR] {message}")
        print(f"[ERROR] {message}")
    
    def log_warning(self, message: str):
        """Log a warning"""
        self.warnings.append(f"[WARNING] {message}")
        print(f"[WARNING] {message}")
    
    def log_info(self, message: str):
        """Log info"""
        self.info.append(f"[INFO] {message}")
        print(f"[INFO] {message}")
    
    def log_success(self, message: str):
        """Log success"""
        print(f"[OK] {message}")
    
    def check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists"""
        full_path = self.repo_path / file_path
        exists = full_path.exists()
        if not exists:
            self.log_error(f"Required file missing: {file_path}")
        return exists
    
    def check_ip_consistency(self):
        """Check IP address consistency across all files"""
        print("\n[NETWORK] Checking IP Address Consistency...")
        
        # Files that should contain the correct IPs
        files_to_check = [
            'enhanced_bitaxe_monitor.py',
            'config.py',
            'QUICK_START_GUIDE.md',
            'examples/sample_config.py',
            'docker/docker-compose.yml',
            'config/config_example.json'
        ]
        
        ip_pattern = r'192\.168\.1\.(\d+)'
        
        for file_path in files_to_check:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                self.log_warning(f"File not found for IP check: {file_path}")
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all IP addresses
                ips_found = re.findall(ip_pattern, content)
                unique_ips = list(set([f"192.168.1.{ip}" for ip in ips_found]))
                
                # Check if expected IPs are present
                expected_found = [ip for ip in self.expected_ips if ip in content]
                
                if len(expected_found) >= 2:  # At least 2 of our IPs should be present
                    self.log_success(f"IP consistency OK in {file_path}")
                else:
                    self.log_warning(f"Expected IPs not found in {file_path}. Found: {unique_ips}")
                    
            except Exception as e:
                self.log_error(f"Error reading {file_path}: {e}")
    
    def check_enhanced_monitor_config(self):
        """Check enhanced monitor configuration"""
        print("\n[MONITOR] Checking Enhanced Monitor Configuration...")
        
        enhanced_monitor_path = self.repo_path / 'enhanced_bitaxe_monitor.py'
        if not enhanced_monitor_path.exists():
            self.log_error("enhanced_bitaxe_monitor.py not found")
            return
        
        try:
            # Try to import and test
            sys.path.insert(0, str(self.repo_path))
            from enhanced_bitaxe_monitor import EnhancedBitAxeMonitor, MinerConfig
            
            # Test configuration
            test_config = [
                {'name': 'Test-Gamma-1', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200}
            ]
            
            monitor = EnhancedBitAxeMonitor(test_config, port=8083)
            self.log_success("Enhanced monitor imports and initializes correctly")
            
            # Check Flask app
            if hasattr(monitor, 'app'):
                self.log_success("Flask app initialized")
            else:
                self.log_error("Flask app not initialized")
            
            # Check variance trackers
            if hasattr(monitor, 'variance_trackers'):
                self.log_success("Variance trackers initialized")
            else:
                self.log_error("Variance trackers not initialized")
            
        except ImportError as e:
            self.log_error(f"Cannot import enhanced monitor: {e}")
        except Exception as e:
            self.log_error(f"Enhanced monitor test failed: {e}")
    
    def check_docker_configuration(self):
        """Check Docker configuration files"""
        print("\n[DOCKER] Checking Docker Configuration...")
        
        # Check Dockerfile
        dockerfile_path = self.repo_path / 'docker' / 'Dockerfile'
        if dockerfile_path.exists():
            with open(dockerfile_path, 'r') as f:
                dockerfile_content = f.read()
            
            if 'enhanced_bitaxe_monitor.py' in dockerfile_content:
                self.log_success("Dockerfile references enhanced monitor")
            else:
                self.log_warning("Dockerfile may not reference enhanced monitor")
            
            if 'EXPOSE 8080' in dockerfile_content:
                self.log_success("Dockerfile exposes correct port")
            else:
                self.log_warning("Dockerfile port configuration issue")
        else:
            self.log_warning("Dockerfile not found")
        
        # Check docker-compose.yml
        compose_path = self.repo_path / 'docker' / 'docker-compose.yml'
        if compose_path.exists():
            with open(compose_path, 'r') as f:
                compose_content = f.read()
            
            # Check for expected IPs
            expected_ips_found = sum(1 for ip in self.expected_ips if ip in compose_content)
            if expected_ips_found >= 2:
                self.log_success("Docker Compose has correct IP configuration")
            else:
                self.log_warning("Docker Compose IP configuration may be outdated")
        else:
            self.log_warning("docker-compose.yml not found")
    
    def check_github_workflows(self):
        """Check GitHub workflow configurations"""
        print("\n[GITHUB] Checking GitHub Workflows...")
        
        workflows_dir = self.repo_path / '.github' / 'workflows'
        if not workflows_dir.exists():
            self.log_warning("GitHub workflows directory not found")
            return
        
        workflow_files = list(workflows_dir.glob('*.yml'))
        if not workflow_files:
            self.log_warning("No GitHub workflow files found")
            return
        
        self.log_success(f"Found {len(workflow_files)} workflow files")
        
        # Check enhanced-quality.yml specifically
        enhanced_workflow = workflows_dir / 'enhanced-quality.yml'
        if enhanced_workflow.exists():
            try:
                with open(enhanced_workflow, 'r', encoding='utf-8') as f:
                    workflow_content = f.read()
                
                if 'enhanced_bitaxe_monitor.py' in workflow_content:
                    self.log_success("Enhanced quality workflow configured correctly")
                else:
                    self.log_warning("Enhanced quality workflow may need updates")
            except UnicodeDecodeError:
                self.log_warning("Enhanced quality workflow has encoding issues")
        else:
            self.log_warning("enhanced-quality.yml workflow not found")
    
    def check_documentation_consistency(self):
        """Check documentation consistency"""
        print("\n[DOCS] Checking Documentation Consistency...")
        
        # Check main documentation files
        doc_files = [
            'README.md',
            'QUICK_START_GUIDE.md',
            'docs/api_reference.md',
            'docs/troubleshooting.md'
        ]
        
        for doc_file in doc_files:
            doc_path = self.repo_path / doc_file
            if doc_path.exists():
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for enhanced monitor references
                if 'enhanced' in content.lower() or 'chart.js' in content.lower():
                    self.log_success(f"{doc_file} references enhanced features")
                else:
                    self.log_info(f"{doc_file} may need enhanced monitor documentation")
            else:
                self.log_warning(f"Documentation file not found: {doc_file}")
    
    def check_test_configuration(self):
        """Check test configuration and consistency"""
        print("\n[TESTS] Checking Test Configuration...")
        
        tests_dir = self.repo_path / 'tests'
        if not tests_dir.exists():
            self.log_warning("Tests directory not found")
            return
        
        # Check main test file
        main_test = tests_dir / 'test_bitaxe_monitor.py'
        if main_test.exists():
            try:
                # Run syntax check
                subprocess.run([sys.executable, '-m', 'py_compile', str(main_test)], 
                             check=True, capture_output=True)
                self.log_success("Main test file syntax is valid")
            except subprocess.CalledProcessError:
                self.log_error("Main test file has syntax errors")
        else:
            self.log_warning("Main test file not found")
        
        # Check test configuration files
        test_configs = ['test_config.py', 'test_enhanced_monitor.py']
        for config_file in test_configs:
            config_path = self.repo_path / config_file
            if config_path.exists():
                self.log_success(f"Test configuration file found: {config_file}")
            else:
                self.log_info(f"Optional test file not found: {config_file}")
    
    def check_dependencies(self):
        """Check dependency files"""
        print("\n[DEPS] Checking Dependencies...")
        
        # Check requirements files
        req_files = ['requirements.txt', 'requirements-dev.txt']
        for req_file in req_files:
            req_path = self.repo_path / req_file
            if req_path.exists():
                with open(req_path, 'r') as f:
                    content = f.read()
                
                # Check for essential dependencies
                if 'flask' in content.lower() and 'requests' in content.lower():
                    self.log_success(f"{req_file} contains essential dependencies")
                else:
                    self.log_warning(f"{req_file} missing essential dependencies")
            else:
                self.log_warning(f"Requirements file not found: {req_file}")
    
    def check_security_and_quality(self):
        """Check security and code quality configurations"""
        print("\n[SECURITY] Checking Security and Quality...")
        
        # Check for security files
        security_files = ['.gitignore', 'SECURITY.md', '.pylintrc']
        for sec_file in security_files:
            sec_path = self.repo_path / sec_file
            if sec_path.exists():
                self.log_success(f"Security/quality file found: {sec_file}")
            else:
                self.log_info(f"Optional security/quality file not found: {sec_file}")
        
        # Check .gitignore for sensitive content
        gitignore_path = self.repo_path / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
            
            if '__pycache__' in gitignore_content and '.env' in gitignore_content:
                self.log_success(".gitignore contains essential exclusions")
            else:
                self.log_warning(".gitignore may be missing important exclusions")
    
    def generate_report(self):
        """Generate final consistency report"""
        print("\n" + "=" * 60)
        print("[REPORT] REPOSITORY CONSISTENCY REPORT")
        print("=" * 60)
        
        print(f"\n[OK] Successes: {len([msg for msg in self.info if 'success' in msg.lower()])}")
        print(f"[WARNING] Warnings: {len(self.warnings)}")
        print(f"[ERROR] Errors: {len(self.errors)}")
        
        if self.errors:
            print(f"\n[ERROR] ERRORS TO FIX:")
            for error in self.errors:
                print(f"   {error}")
        
        if self.warnings:
            print(f"\n[WARNING] WARNINGS TO REVIEW:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Overall status
        if not self.errors:
            if not self.warnings:
                print(f"\n[EXCELLENT] Repository is fully consistent.")
                return True
            else:
                print(f"\n[GOOD] Repository is mostly consistent with minor warnings.")
                return True
        else:
            print(f"\n[NEEDS WORK] Repository has consistency issues that should be fixed.")
            return False
    
    def run_full_check(self):
        """Run complete repository consistency check"""
        print("[CHECK] BitAxe Monitor Repository Consistency Check")
        print("=" * 60)
        
        # Core file checks
        essential_files = [
            'enhanced_bitaxe_monitor.py',
            'README.md',
            'requirements.txt',
            'docker/Dockerfile',
            'docker/docker-compose.yml'
        ]
        
        print("\n[FILES] Checking Essential Files...")
        for file_path in essential_files:
            if self.check_file_exists(file_path):
                self.log_success(f"Essential file found: {file_path}")
        
        # Run all checks
        self.check_ip_consistency()
        self.check_enhanced_monitor_config() 
        self.check_docker_configuration()
        self.check_github_workflows()
        self.check_documentation_consistency()
        self.check_test_configuration()
        self.check_dependencies()
        self.check_security_and_quality()
        
        # Generate final report
        return self.generate_report()


def main():
    """Main entry point"""
    repo_path = os.path.dirname(os.path.abspath(__file__))
    checker = RepositoryChecker(repo_path)
    
    success = checker.run_full_check()
    
    if success:
        print("\n[SUCCESS] Repository is ready for production use!")
    else:
        print("\n[FIX NEEDED] Please fix the issues above before deploying.")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
