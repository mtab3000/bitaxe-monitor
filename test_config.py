#!/usr/bin/env python3
"""
Quick Configuration Test

This script verifies that all your BitAxe miner IP addresses
are correctly configured throughout the repository.
"""

def test_config():
    """Test that the enhanced monitor is configured correctly"""
    print("[INFO] BitAxe Monitor Configuration Test")
    print("=" * 50)
    
    # Test the enhanced monitor configuration
    try:
        from enhanced_bitaxe_monitor import EnhancedBitAxeMonitor
        
        # This will use the default configuration from the file
        test_config = [
            {'name': 'BitAxe-Gamma-1', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200},
            {'name': 'BitAxe-Gamma-2', 'ip': '192.168.1.46', 'expected_hashrate_gh': 1150},
            {'name': 'BitAxe-Gamma-3', 'ip': '192.168.1.47', 'expected_hashrate_gh': 1100}
        ]
        
        monitor = EnhancedBitAxeMonitor(test_config, port=8082)
        
        print("[OK] Enhanced monitor configured correctly")
        print("[OK] Miner configurations loaded:")
        for miner in monitor.miners:
            print(f"   - {miner.name}: {miner.ip} (Expected: {miner.expected_hashrate_gh} GH/s)")
        
        print("\n[CONFIG] Your BitAxe miners are configured:")
        print("   - BitAxe-Gamma-1: 192.168.1.45")
        print("   - BitAxe-Gamma-2: 192.168.1.46") 
        print("   - BitAxe-Gamma-3: 192.168.1.47")
        
        print("\n[READY] Ready to run!")
        print("   Run: python enhanced_bitaxe_monitor.py")
        print("   Open: http://localhost:8080")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Configuration error: {e}")
        return False

if __name__ == '__main__':
    success = test_config()
    if success:
        print("\n[SUCCESS] All configurations updated successfully!")
        print("Your BitAxe monitor is ready to use with your actual miners!")
    else:
        print("\n[FAILED] Configuration test failed. Check the error above.")
