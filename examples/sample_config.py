#!/usr/bin/env python3
"""
Sample Configuration Examples for Bitaxe Monitor & Visualizer
Copy and modify these configurations for your setup
"""

# =============================================================================
# BASIC CONFIGURATION - 3 Miners on Same Network
# =============================================================================

basic_config = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45'},
    {'name': 'Gamma-2', 'ip': '192.168.1.46'},
    {'name': 'Gamma-3', 'ip': '192.168.1.47'}
]

# =============================================================================
# ADVANCED CONFIGURATION - Mixed Network Setup
# =============================================================================

advanced_config = [
    # Standard miners on default port 80
    {'name': 'Office-Gamma-1', 'ip': '192.168.1.100'},
    {'name': 'Office-Gamma-2', 'ip': '192.168.1.101'},
    
    # Miner with custom port
    {'name': 'Basement-Gamma', 'ip': '192.168.1.200', 'port': 8080},
    
    # Miners on different subnet
    {'name': 'Garage-Gamma-1', 'ip': '192.168.2.50'},
    {'name': 'Garage-Gamma-2', 'ip': '192.168.2.51'},
    
    # Remote miner (ensure network access)
    {'name': 'Remote-Gamma', 'ip': '10.0.1.150'}
]

# =============================================================================
# SINGLE MINER CONFIGURATION - Testing Setup
# =============================================================================

single_miner_config = [
    {'name': 'Test-Gamma', 'ip': '192.168.1.45'}
]

# =============================================================================
# LARGE SCALE CONFIGURATION - Mining Farm Setup
# =============================================================================

farm_config = []

# Generate configurations for multiple racks
for rack in range(1, 4):  # 3 racks
    for position in range(1, 9):  # 8 miners per rack
        farm_config.append({
            'name': f'Rack{rack}-Pos{position}',
            'ip': f'192.168.{rack}.{position + 10}'
        })

# =============================================================================
# HOSTNAME-BASED CONFIGURATION - mDNS Setup
# =============================================================================

hostname_config = [
    {'name': 'Living-Room', 'ip': 'bitaxe-living.local'},
    {'name': 'Office-Desk', 'ip': 'bitaxe-office.local'},
    {'name': 'Basement', 'ip': 'bitaxe-basement.local'}
]

# =============================================================================
# CUSTOM POLLING INTERVALS EXAMPLE
# =============================================================================

class CustomMonitorConfig:
    """Example of custom monitor configuration with different settings"""
    
    def __init__(self):
        self.miners = [
            {'name': 'High-Performance', 'ip': '192.168.1.45'},
            {'name': 'Efficiency-Focused', 'ip': '192.168.1.46'},
            {'name': 'Experimental', 'ip': '192.168.1.47'}
        ]
        
        # Custom polling intervals (seconds)
        self.polling_intervals = {
            'fast': 30,      # For performance monitoring
            'normal': 60,    # Standard monitoring
            'slow': 300      # For stable, long-term monitoring
        }
        
        # Custom timeout settings
        self.timeouts = {
            'connection': 5,  # Connection timeout
            'read': 10       # Read timeout
        }

# =============================================================================
# VISUALIZATION CONFIGURATION EXAMPLES
# =============================================================================

class VisualizationConfig:
    """Example visualization settings"""
    
    def __init__(self):
        # Chart generation options
        self.chart_options = {
            'save_plots': True,
            'show_plots': False,  # Set to False for automated processing
            'dpi': 300,          # High resolution for reports
            'figsize': (16, 12)  # Custom figure size
        }
        
        # Color schemes for different miners
        self.color_schemes = {
            'default': ['#2E8B57', '#FF6347', '#4169E1', '#FFD700', '#8A2BE2', '#FF69B4'],
            'grayscale': ['#000000', '#404040', '#808080', '#A0A0A0', '#C0C0C0', '#E0E0E0'],
            'colorblind_friendly': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        }
        
        # Time formatting options
        self.time_formats = {
            'detailed': '%m/%d %H:%M',
            'simple': '%H:%M',
            'date_only': '%m/%d'
        }

# =============================================================================
# NETWORK DISCOVERY HELPER
# =============================================================================

def discover_bitaxe_miners(network_base='192.168.1', start_ip=1, end_ip=254, port=80):
    """
    Helper function to discover Bitaxe miners on network
    WARNING: This will make HTTP requests to many IPs - use carefully!
    """
    import requests
    import socket
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    discovered_miners = []
    
    def check_ip(ip):
        try:
            # Quick port check first
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:  # Port is open
                # Try to get system info
                response = requests.get(f'http://{ip}:{port}/api/system/info', timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if 'ASICModel' in data:  # Likely a Bitaxe
                        return {
                            'ip': ip,
                            'model': data.get('ASICModel', 'Unknown'),
                            'version': data.get('version', 'Unknown'),
                            'hostname': data.get('hostname', f'bitaxe-{ip.split(".")[-1]}')
                        }
        except:
            pass
        return None
    
    print(f"🔍 Scanning network {network_base}.{start_ip}-{end_ip} for Bitaxe miners...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ip = {
            executor.submit(check_ip, f"{network_base}.{i}"): i 
            for i in range(start_ip, end_ip + 1)
        }
        
        for future in as_completed(future_to_ip):
            result = future.result()
            if result:
                discovered_miners.append(result)
                print(f"✅ Found: {result['ip']} - {result['model']} - {result['hostname']}")
    
    return discovered_miners

# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================

def validate_config(miners_config):
    """Validate miner configuration before use"""
    import socket
    import ipaddress
    
    errors = []
    warnings = []
    
    for i, miner in enumerate(miners_config):
        # Check required fields
        if 'name' not in miner:
            errors.append(f"Miner {i}: Missing 'name' field")
        if 'ip' not in miner:
            errors.append(f"Miner {i}: Missing 'ip' field")
            continue
        
        # Validate IP address
        try:
            if not miner['ip'].endswith('.local'):  # Skip hostname validation
                ipaddress.ip_address(miner['ip'])
        except ValueError:
            errors.append(f"Miner {miner.get('name', i)}: Invalid IP address '{miner['ip']}'")
        
        # Check port
        port = miner.get('port', 80)
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append(f"Miner {miner.get('name', i)}: Invalid port {port}")
        
        # Check for duplicate names
        names = [m['name'] for m in miners_config if 'name' in m]
        if names.count(miner.get('name')) > 1:
            warnings.append(f"Duplicate name '{miner.get('name')}' found")
        
        # Check for duplicate IPs
        ips = [m['ip'] for m in miners_config if 'ip' in m]
        if ips.count(miner.get('ip')) > 1:
            warnings.append(f"Duplicate IP '{miner.get('ip')}' found")
    
    return errors, warnings

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("Bitaxe Configuration Examples")
    print("=" * 50)
    
    # Example 1: Basic validation
    print("\n1. Validating basic configuration...")
    errors, warnings = validate_config(basic_config)
    
    if errors:
        print("❌ Errors found:")
        for error in errors:
            print(f"   {error}")
    
    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"   {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration is valid!")
    
    # Example 2: Network discovery (commented out for safety)
    # print("\n2. Network discovery example...")
    # discovered = discover_bitaxe_miners('192.168.1', 40, 50)
    # print(f"Found {len(discovered)} miners")
    
    # Example 3: Generate config from discovery
    print("\n3. Sample generated configuration:")
    sample_discovered = [
        {'ip': '192.168.1.45', 'model': 'BM1370', 'hostname': 'bitaxe-45'},
        {'ip': '192.168.1.46', 'model': 'BM1370', 'hostname': 'bitaxe-46'},
        {'ip': '192.168.1.47', 'model': 'BM1370', 'hostname': 'bitaxe-47'}
    ]
    
    generated_config = []
    for i, miner in enumerate(sample_discovered):
        generated_config.append({
            'name': f"Gamma-{i+1}",
            'ip': miner['ip']
        })
    
    print("Generated configuration:")
    for miner in generated_config:
        print(f"   {miner}")
    
    print("\n4. Configuration file sizes:")
    configs = {
        'Basic (3 miners)': basic_config,
        'Advanced (6 miners)': advanced_config,
        'Farm (24 miners)': farm_config
    }
    
    for name, config in configs.items():
        print(f"   {name}: {len(config)} miners")
