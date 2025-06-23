# BitAxe Monitor Configuration
# Edit this file to set up your BitAxe miners

MINERS_CONFIG = [
    # Example configurations - edit these with your actual miner details
    {'name': 'BitAxe-Gamma-1', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200},
    {'name': 'BitAxe-Gamma-2', 'ip': '192.168.1.46', 'expected_hashrate_gh': 1150},
    {'name': 'BitAxe-Gamma-3', 'ip': '192.168.1.47', 'expected_hashrate_gh': 1100},
    
    # Add more miners as needed:
    # {'name': 'BitAxe-Supra-1', 'ip': '192.168.1.48', 'expected_hashrate_gh': 700},
    # {'name': 'BitAxe-Ultra-1', 'ip': '192.168.1.49', 'expected_hashrate_gh': 500},
]

# Web server configuration
WEB_PORT = 8080
WEB_HOST = '127.0.0.1'  # Default to localhost for security
# Change to '0.0.0.0' only if you need external access and have proper security measures

# API timeout settings
API_TIMEOUT = 5  # seconds

# Variance tracking settings
VARIANCE_HISTORY_SIZE = 600  # Keep 10 minutes of data points
