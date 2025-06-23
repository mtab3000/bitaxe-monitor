#!/usr/bin/env python3
"""
Quick Fix Demo - Web Interface Debug

This creates a minimal working demo with debugging to identify interface issues.
"""

import sys
import os
import time
import random
import json
from datetime import datetime
from flask import Flask, jsonify, render_template_string

# Simple test web server
app = Flask(__name__)

# Simple HTML with debugging
HTML_DEBUG = '''
<!DOCTYPE html>
<html>
<head>
    <title>Bitaxe Monitor - Debug Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .miner-card { border: 1px solid #ccc; margin: 10px; padding: 15px; border-radius: 8px; }
        .online { border-color: #28a745; background: #f8fff9; }
        .loading { color: #666; font-style: italic; }
        .error { color: red; font-weight: bold; }
        .success { color: green; font-weight: bold; }
        #debug { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Bitaxe Monitor - Debug Test</h1>
    
    <div id="debug">
        <h3>Debug Info:</h3>
        <div id="debugInfo">Starting...</div>
    </div>
    
    <div id="updateTime" class="loading">Loading...</div>
    
    <div id="statsGrid">
        <div class="miner-card">
            <div class="loading">Waiting for data...</div>
        </div>
    </div>
    
    <div id="minersGrid">
        <!-- Miners will appear here -->
    </div>
    
    <script>
        function debugLog(message) {
            const debugInfo = document.getElementById('debugInfo');
            const timestamp = new Date().toLocaleTimeString();
            debugInfo.innerHTML += '<br>' + timestamp + ': ' + message;
            console.log(message);
        }
        
        function updateData() {
            debugLog('updateData() called');
            
            fetch('/api/metrics')
                .then(response => {
                    debugLog('API response received: ' + response.status);
                    return response.json();
                })
                .then(data => {
                    debugLog('Data parsed successfully');
                    debugLog('Miners found: ' + data.miners.length);
                    
                    // Update timestamp
                    document.getElementById('updateTime').textContent = 
                        'Last updated: ' + new Date(data.timestamp).toLocaleString();
                    document.getElementById('updateTime').className = 'success';
                    
                    // Create miners HTML
                    let minersHtml = '';
                    data.miners.forEach(miner => {
                        minersHtml += `
                            <div class="miner-card online">
                                <h3>${miner.miner_name}</h3>
                                <div><strong>Status:</strong> ${miner.status}</div>
                                <div><strong>Hashrate:</strong> ${miner.hashrate_th.toFixed(3)} TH/s</div>
                                <div><strong>Efficiency:</strong> ${miner.hashrate_efficiency_pct.toFixed(1)}%</div>
                                <div><strong>Power:</strong> ${miner.power_w.toFixed(1)} W</div>
                                <div><strong>Temperature:</strong> ${miner.temperature_c.toFixed(1)}C</div>
                                <div><strong>Expected:</strong> ${miner.expected_hashrate_th.toFixed(3)} TH/s</div>
                                <div><strong>Deviation:</strong> ${(miner.hashrate_gh - miner.expected_hashrate_gh).toFixed(1)} GH/s</div>
                            </div>
                        `;
                    });
                    
                    document.getElementById('minersGrid').innerHTML = minersHtml;
                    debugLog('Interface updated successfully');
                })
                .catch(error => {
                    debugLog('ERROR: ' + error.message);
                    document.getElementById('updateTime').textContent = 'Error: ' + error.message;
                    document.getElementById('updateTime').className = 'error';
                });
        }
        
        // Initial update
        debugLog('Starting debug interface');
        updateData();
        
        // Update every 5 seconds
        setInterval(updateData, 5000);
        debugLog('Update interval set to 5 seconds');
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """
    Serve the HTML debug interface for monitoring simulated mining devices.
    
    Returns:
        str: The rendered HTML page for the Bitaxe Monitor debug interface.
    """
    return render_template_string(HTML_DEBUG)

@app.route('/api/metrics')
def api_metrics():
    # Generate demo data
    """
    Return simulated miner metrics as a JSON response for debugging and demonstration.
    
    The response contains randomized data for three miners, including hashrate, power, temperature, frequency, uptime, and status, as well as aggregate totals and a timestamp.
    """
    miners = []
    for i in range(1, 4):
        base_hashrate = [1200, 1150, 1100][i-1]
        variance = random.uniform(-50, 80)
        actual_hashrate = max(0, base_hashrate + variance)
        
        miner = {
            'miner_name': f'Demo-Gamma-{i}',
            'miner_ip': f'127.0.0.{i}',
            'status': 'ONLINE',
            'hashrate_gh': actual_hashrate,
            'hashrate_th': actual_hashrate / 1000,
            'expected_hashrate_gh': base_hashrate,
            'expected_hashrate_th': base_hashrate / 1000,
            'hashrate_efficiency_pct': (actual_hashrate / base_hashrate) * 100,
            'power_w': random.uniform(13, 16),
            'temperature_c': random.uniform(55, 75),
            'frequency_mhz': random.randint(485, 510),
            'uptime_s': 300
        }
        miners.append(miner)
    
    response = {
        'timestamp': datetime.now().isoformat(),
        'total_hashrate_th': sum(m['hashrate_th'] for m in miners),
        'total_power_w': sum(m['power_w'] for m in miners),
        'online_count': len(miners),
        'total_count': len(miners),
        'miners': miners
    }
    
    return jsonify(response)

if __name__ == '__main__':
    print("=" * 60)
    print("QUICK DEBUG TEST - Bitaxe Monitor Interface")
    print("=" * 60)
    print("This is a minimal test to debug the web interface")
    print()
    print("1. Open browser: http://localhost:8080")
    print("2. Check debug messages on the page")
    print("3. Verify miners are showing")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8080, debug=False)
