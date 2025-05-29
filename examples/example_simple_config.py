#!/usr/bin/env python3
"""
Simple Bitaxe Configuration Template
Copy this file and modify for your setup
"""

# =============================================================================
# QUICK START CONFIGURATION
# =============================================================================

# Replace these IP addresses with your actual Bitaxe miner IPs
MINERS = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45'},
    {'name': 'Gamma-2', 'ip': '192.168.1.46'},
    {'name': 'Gamma-3', 'ip': '192.168.1.47'}
]

# =============================================================================
# SETTINGS
# =============================================================================

# Monitoring settings
POLLING_INTERVAL = 60  # seconds between updates
TIMEOUT = 5           # seconds to wait for miner response
SHOW_DETAILED = False # Set to True for verbose output

# Visualization settings  
SAVE_CHARTS = True    # Save PNG files
SHOW_CHARTS = False   # Display charts on screen (set False for headless)
CHART_DPI = 300      # Resolution for saved charts

# =============================================================================
# NETWORK DISCOVERY (OPTIONAL)
# =============================================================================

# Uncomment and modify to auto-discover miners on your network
# NETWORK_BASE = '192.168.1'  # Your network subnet
# IP_START = 1                # Start IP range
# IP_END = 254               # End IP range

# =============================================================================
# HOW TO USE THIS FILE
# =============================================================================

"""
1. Copy this file to your project directory
2. Modify the MINERS list with your actual IP addresses
3. Test connectivity: python test_config.py
4. Run monitor: python bitaxe_monitor.py
5. Generate charts: python bitaxe_visualizer.py

FINDING YOUR MINER IPs:
- Check your router's admin panel for connected devices
- Look for devices named "bitaxe" or with MAC addresses starting with ESP32
- Try common IPs: 192.168.1.x, 192.168.0.x, 10.0.0.x
- Use network scanner: nmap -sn 192.168.1.0/24

TESTING:
Run this file directly to test your configuration:
python simple_config.py
"""

# =============================================================================
# CONFIGURATION TESTER
# =============================================================================

def test_configuration():
    """Test the configuration by attempting to connect to each miner"""
    import requests
    import socket
    
    print("🔧 Testing Bitaxe Configuration")
    print("=" * 50)
    
    success_count = 0
    
    for miner in MINERS:
        name = miner['name']
        ip = miner['ip']
        port = miner.get('port', 80)
        
        print(f"\n🔥 Testing {name} ({ip}:{port})")
        
        # Test 1: Ping connectivity
        import os
        ping_result = os.system(f"ping -c 1 -W 1000 {ip} >/dev/null 2>&1")
        if ping_result == 0:
            print("  ✅ Ping: Reachable")
        else:
            print("  ❌ Ping: Unreachable")
            continue
        
        # Test 2: Port connectivity
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(TIMEOUT)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                print(f"  ✅ Port {port}: Open")
            else:
                print(f"  ❌ Port {port}: Closed")
                continue
                
        except Exception as e:
            print(f"  ❌ Port {port}: Error - {e}")
            continue
        
        # Test 3: API connectivity
        try:
            url = f"http://{ip}:{port}/api/system/info"
            response = requests.get(url, timeout=TIMEOUT)
            
            if response.status_code == 200:
                print("  ✅ API: Responding")
                
                data = response.json()
                model = data.get('ASICModel', 'Unknown')
                version = data.get('version', 'Unknown')
                hashrate = data.get('hashRate', 0)
                temp = data.get('temp', 0)
                
                print(f"    📋 Model: {model}")
                print(f"    💾 Firmware: {version}")
                print(f"    ⚡ Hashrate: {hashrate/1000:.3f} TH/s")
                print(f"    🌡️  Temperature: {temp}°C")
                
                success_count += 1
                
            else:
                print(f"  ❌ API: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectTimeout:
            print("  ❌ API: Connection timeout")
        except requests.exceptions.ConnectionError:
            print("  ❌ API: Connection error")
        except Exception as e:
            print(f"  ❌ API: Error - {e}")
    
    print(f"\n📊 Summary: {success_count}/{len(MINERS)} miners configured correctly")
    
    if success_count == len(MINERS):
        print("🎉 All miners configured successfully!")
        print("\n🚀 Next steps:")
        print("   1. Run: python bitaxe_monitor.py")
        print("   2. Wait 5-10 minutes for data collection")
        print("   3. Run: python bitaxe_visualizer.py")
    else:
        print("⚠️  Some miners need configuration fixes")
        print("\n🔧 Troubleshooting:")
        print("   - Check IP addresses are correct")
        print("   - Ensure miners are powered on")
        print("   - Verify network connectivity")
        print("   - Check firewall settings")

def generate_config_from_network():
    """Scan network and generate configuration automatically"""
    import requests
    import socket
    from concurrent.futures import ThreadPoolExecutor
    
    network_base = input("Enter network base (e.g., 192.168.1): ").strip()
    if not network_base:
        network_base = "192.168.1"
    
    print(f"🔍 Scanning network {network_base}.1-254 for Bitaxe miners...")
    
    found_miners = []
    
    def check_ip(ip):
        try:
            # Quick port check
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, 80))
            sock.close()
            
            if result == 0:
                # Try API
                response = requests.get(f'http://{ip}/api/system/info', timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if 'ASICModel' in data:
                        return {
                            'ip': ip,
                            'model': data.get('ASICModel', 'Unknown'),
                            'hostname': data.get('hostname', f'bitaxe-{ip.split(".")[-1]}')
                        }
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(check_ip, f"{network_base}.{i}") 
            for i in range(1, 255)
        ]
        
        for future in futures:
            result = future.result()
            if result:
                found_miners.append(result)
                print(f"✅ Found: {result['ip']} - {result['model']} - {result['hostname']}")
    
    if found_miners:
        print(f"\n🎉 Found {len(found_miners)} Bitaxe miners!")
        print("\nGenerated configuration:")
        print("MINERS = [")
        for i, miner in enumerate(found_miners):
            name = f"Gamma-{i+1}"
            print(f"    {{'name': '{name}', 'ip': '{miner['ip']}'}},")
        print("]")
        
        save = input("\nSave this configuration to config.py? (y/n): ").lower()
        if save == 'y':
            with open('generated_config.py', 'w') as f:
                f.write("# Auto-generated Bitaxe configuration\n\n")
                f.write("MINERS = [\n")
                for i, miner in enumerate(found_miners):
                    name = f"Gamma-{i+1}"
                    f.write(f"    {{'name': '{name}', 'ip': '{miner['ip']}'}},\n")
                f.write("]\n")
            print("✅ Configuration saved to generated_config.py")
    else:
        print("❌ No Bitaxe miners found on network")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("Bitaxe Configuration Helper")
    print("=" * 30)
    
    print("\nOptions:")
    print("1. Test current configuration")
    print("2. Auto-discover miners on network")
    print("3. Show configuration help")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_configuration()
    elif choice == "2":
        generate_config_from_network()
    elif choice == "3":
        print(__doc__)
    else:
        print("Invalid choice. Testing current configuration...")
        test_configuration()
