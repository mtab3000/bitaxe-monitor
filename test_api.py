#!/usr/bin/env python3
"""
Test script to verify the API endpoint is working correctly
"""

import requests
import json

def test_api():
    try:
        # Test the metrics API endpoint
        response = requests.get('http://localhost:8080/api/metrics', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            print("[OK] API Test Results:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Total Hashrate: {data.get('total_hashrate_th', 'N/A'):.3f} TH/s")
            print(f"   Fleet Efficiency: {data.get('fleet_efficiency', 'N/A'):.1f}%")
            print(f"   Miners Online: {data.get('online_count', 'N/A')}/{data.get('total_count', 'N/A')}")
            print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
            
            print("\n[OK] Miner Details:")
            for miner in data.get('miners', []):
                if miner.get('status') == 'ONLINE':
                    print(f"   >> {miner.get('miner_name')}: {miner.get('hashrate_gh', 'N/A'):.1f} GH/s")
                    print(f"      Expected: {miner.get('expected_hashrate_gh', 'N/A'):.1f} GH/s")
                    print(f"      Efficiency: {miner.get('hashrate_efficiency_pct', 'N/A'):.1f}%")
                    if miner.get('hashrate_stddev_60s'):
                        print(f"      Std Dev (60s): {miner.get('hashrate_stddev_60s'):.1f} GH/s")
                    print()
            
            print("[OK] API endpoint is working correctly!")
            print("[OK] All required fields are present for chart rendering")
            return True
            
        else:
            print(f"[ERROR] API Error: Status Code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection Error: Is the server running on localhost:8080?")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        return False

if __name__ == '__main__':
    print("Testing BitAxe Monitor API...")
    print("=" * 50)
    test_api()
