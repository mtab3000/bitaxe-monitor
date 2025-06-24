#!/usr/bin/env python3
"""
Test script to check BitAxe API response fields
"""

import requests
import json

# Test miner IP
MINER_IP = "192.168.1.45"

print("🔍 Testing BitAxe API response...")
print(f"Connecting to: http://{MINER_IP}/api/system/info\n")

try:
    response = requests.get(f'http://{MINER_IP}/api/system/info', timeout=5)
    response.raise_for_status()
    data = response.json()
    
    print("✅ Successfully connected to BitAxe miner!\n")
    print("📊 Available API fields:")
    print("-" * 50)
    
    for key, value in sorted(data.items()):
        print(f"{key:<25}: {value}")
    
    print("\n🔍 Voltage-related fields:")
    print("-" * 50)
    for key, value in data.items():
        if 'volt' in key.lower() or 'voltage' in key.lower():
            print(f"{key:<25}: {value}")
    
    # Pretty print the full response
    print("\n📄 Full API Response (formatted):")
    print("-" * 50)
    print(json.dumps(data, indent=2))
    
except requests.exceptions.RequestException as e:
    print(f"❌ Error connecting to miner: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
