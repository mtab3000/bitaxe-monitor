# Troubleshooting Guide

This guide covers common issues and solutions for the Bitaxe Monitor & Visualizer tools.

## 🚨 Quick Diagnostic Checklist

Before diving into specific issues, run through this quick checklist:

- [ ] **Python version**: 3.6 or higher (`python --version`)
- [ ] **Dependencies installed**: `pip install -r requirements.txt`
- [ ] **Network connectivity**: Can you ping your miners?
- [ ] **Web interface access**: Can you access miner web interface in browser?
- [ ] **IP addresses correct**: Double-check miner IPs in configuration
- [ ] **Firewalls disabled**: Temporarily disable firewalls for testing

---

## 🔌 Connection & Network Issues

### ❌ "Connection refused" / "Connection timeout"

**Symptoms:**
```
❌ Error fetching data from Gamma-1 (192.168.1.45): HTTPConnectionPool(host='192.168.1.45', port=80): Max retries exceeded
```

**Solutions:**

1. **Verify IP Address**
   ```bash
   # Check if miner responds to ping
   ping 192.168.1.45
   
   # Check if HTTP port is open
   telnet 192.168.1.45 80
   ```

2. **Check Miner Web Interface**
   - Open `http://192.168.1.45` in your browser
   - Should show Bitaxe web interface
   - If not accessible, miner may be offline or IP changed

3. **Network Troubleshooting**
   ```bash
   # Find devices on network (Linux/Mac)
   nmap -sn 192.168.1.0/24
   
   # Windows equivalent
   for /l %i in (1,1,254) do @ping -n 1 -w 100 192.168.1.%i | find "Reply"
   ```

4. **Port Configuration**
   ```python
   # If miner uses non-standard port
   {'name': 'Gamma-1', 'ip': '192.168.1.45', 'port': 8080}
   ```

5. **Firewall Issues**
   ```bash
   # Temporarily disable Windows Firewall
   netsh advfirewall set allprofiles state off
   
   # Re-enable after testing
   netsh advfirewall set allprofiles state on
   ```

### ❌ "No route to host" / "Network unreachable"

**Solutions:**

1. **Check Network Interfaces**
   ```bash
   # Show network configuration
   ipconfig    # Windows
   ifconfig    # Linux/Mac
   ```

2. **Verify Subnet**
   - Ensure computer and miners are on same network
   - Check router DHCP settings
   - Verify no VLAN isolation

3. **Router Configuration**
   - Check if AP isolation is enabled (disable it)
   - Verify port forwarding isn't interfering
   - Check guest network restrictions

---

## 🐍 Python Environment Issues

### ❌ "No module named 'requests'"

**Solutions:**

1. **Install Dependencies**
   ```bash
   pip install requests
   # Or install all dependencies
   pip install -r requirements.txt
   ```

2. **Virtual Environment Issues**
   ```bash
   # Create virtual environment
   python -m venv bitaxe_env
   
   # Activate (Windows)
   bitaxe_env\Scripts\activate
   
   # Activate (Linux/Mac)
   source bitaxe_env/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Multiple Python Versions**
   ```bash
   # Use specific Python version
   python3 -m pip install requests
   python3 bitaxe_monitor.py
   ```

### ❌ "ModuleNotFoundError: No module named 'matplotlib'"

**Solutions:**

1. **Install Visualization Dependencies**
   ```bash
   pip install matplotlib pandas numpy
   ```

2. **System-specific Issues**
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt-get install python3-matplotlib python3-pandas
   ```
   
   **macOS:**
   ```bash
   brew install python-tk
   pip install matplotlib
   ```
   
   **Windows:**
   ```bash
   # Use conda if pip fails
   conda install matplotlib pandas numpy
   ```

### ❌ "Permission denied" when saving files

**Solutions:**

1. **Check Directory Permissions**
   ```bash
   # Linux/Mac
   chmod 755 .
   
   # Windows: Right-click folder → Properties → Security
   ```

2. **Run from User Directory**
   ```bash
   cd ~/Documents
   python /path/to/bitaxe_monitor.py
   ```

3. **Specify Output Directory**
   ```python
   # Modify script to save in user directory
   import os
   csv_filename = os.path.expanduser(f"~/bitaxe_data_{timestamp}.csv")
   ```

---

## 📊 Data & CSV Issues

### ❌ "No CSV files found"

**Solutions:**

1. **Check File Location**
   ```bash
   # List CSV files in current directory
   ls multi_bitaxe_kpis_*.csv    # Linux/Mac
   dir multi_bitaxe_kpis_*.csv   # Windows
   ```

2. **Run Monitor First**
   ```bash
   # Generate data before visualization
   python bitaxe_monitor.py
   # Let run for at least 2-3 minutes, then Ctrl+C
   python bitaxe_visualizer.py
   ```

3. **Specify CSV Path**
   ```bash
   python bitaxe_visualizer.py --csv /full/path/to/file.csv
   ```

### ❌ "No online miner data found"

**Solutions:**

1. **Check Status Column**
   ```python
   # Debug CSV content
   import pandas as pd
   df = pd.read_csv('your_file.csv')
   print(df['status'].value_counts())
   ```

2. **Verify Monitor Ran Successfully**
   - Check CSV file has data rows (not just headers)
   - Ensure miners were online during monitoring
   - Check for network issues during data collection

### ❌ CSV File Corruption

**Symptoms:**
```
UnicodeDecodeError: 'utf-8' codec can't decode byte
```

**Solutions:**

1. **Check File Encoding**
   ```python
   # Try different encodings
   df = pd.read_csv('file.csv', encoding='latin1')
   # or
   df = pd.read_csv('file.csv', encoding='cp1252')
   ```

2. **Regenerate CSV**
   - Delete corrupted file
   - Run monitor to generate new data

---

## 📈 Visualization Issues

### ❌ "Not enough data points" for graphs

**Solutions:**

1. **Collect More Data**
   ```bash
   # Run monitor longer
   python bitaxe_monitor.py
   # Wait at least 5-10 minutes for multiple data points
   ```

2. **Check Data Quality**
   ```python
   # Verify data in CSV
   import pandas as pd
   df = pd.read_csv('your_file.csv')
   print(f"Total rows: {len(df)}")
   print(f"Online rows: {len(df[df['status'] == 'ONLINE'])}")
   print(f"Miners: {df['miner_name'].unique()}")
   ```

### ❌ Matplotlib Display Issues

**Linux (WSL/Headless):**
```bash
# Install X11 forwarding
sudo apt-get install python3-tk

# Or use non-interactive backend
export MPLBACKEND=Agg
python bitaxe_visualizer.py --no-show
```

**macOS:**
```bash
# Install tkinter
brew install python-tk
```

**Windows:**
```bash
# Usually works out of the box
# If issues, try:
pip uninstall matplotlib
pip install matplotlib
```

### ❌ "Figure size too large" errors

**Solutions:**

1. **Reduce Figure Size**
   ```python
   # Modify in script
   plt.rcParams['figure.figsize'] = (12, 8)  # Smaller size
   ```

2. **Increase Memory**
   ```bash
   # Close other applications
   # Or modify script to generate charts separately
   ```

---

## ⚡ Performance Issues

### 🐌 Slow Monitoring Performance

**Solutions:**

1. **Reduce Polling Frequency**
   ```python
   # Change from 60 to 120 seconds
   time.sleep(120)
   ```

2. **Optimize Network**
   - Use wired connection instead of WiFi
   - Ensure miners and computer on same switch
   - Check for network congestion

3. **Reduce Concurrent Miners**
   ```python
   # Monitor fewer miners simultaneously
   miners_config = miners_config[:5]  # First 5 only
   ```

### 📊 Large CSV Files

**Solutions:**

1. **File Rotation**
   ```python
   # Add to monitor script
   max_file_size = 10 * 1024 * 1024  # 10MB
   if os.path.getsize(csv_filename) > max_file_size:
       # Start new file
   ```

2. **Data Cleanup**
   ```bash
   # Keep only recent data
   tail -n 1000 old_file.csv > recent_data.csv
   ```

---

## 🔧 Hardware-Specific Issues

### Bitaxe Gamma Issues

1. **API Endpoint Differences**
   ```python
   # Some firmware versions use different fields
   # Check actual API response:
   print(json.dumps(response.json(), indent=2))
   ```

2. **Firmware Compatibility**
   - Ensure firmware v2.0+ for full API support
   - Update firmware if needed
   - Check release notes for API changes

### Network Configuration

1. **DHCP vs Static IP**
   ```bash
   # Set static IP on miner to prevent IP changes
   # Access miner web interface → Network settings
   ```

2. **Port Conflicts**
   - Ensure port 80 not used by other services
   - Check for reverse proxies or load balancers

---

## 🔍 Advanced Debugging

### Enable Verbose Logging

```python
import logging

# Add to top of script
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bitaxe_debug.log'),
        logging.StreamHandler()
    ]
)

# Add debug prints
logger = logging.getLogger(__name__)
logger.debug(f"Connecting to {miner['ip']}")
```

### API Response Debugging

```python
# Add to get_bitaxe_data method
try:
    response = requests.get(url, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Content: {response.text[:500]}...")
    return response.json()
except Exception as e:
    print(f"Full error details: {str(e)}")
    import traceback
    traceback.print_exc()
```

### Network Packet Capture

```bash
# Capture HTTP traffic (Linux/Mac)
tcpdump -i any -A -s 0 'host 192.168.1.45 and port 80'

# Windows (requires Wireshark)
# Filter: ip.addr == 192.168.1.45 and tcp.port == 80
```

---

## 📱 Platform-Specific Issues

### Windows Issues

1. **Path Separators**
   ```python
   import os
   csv_path = os.path.join('data', 'file.csv')  # Correct
   # Not: csv_path = 'data/file.csv'
   ```

2. **Antivirus Interference**
   - Temporarily disable antivirus
   - Add Python/script directory to exclusions

3. **PowerShell vs Command Prompt**
   ```powershell
   # Use PowerShell for better Unicode support
   python bitaxe_monitor.py
   ```

### macOS Issues

1. **Certificate Errors**
   ```bash
   # Update certificates
   /Applications/Python\ 3.x/Install\ Certificates.command
   ```

2. **Permission Issues**
   ```bash
   # Grant Python network access
   # System Preferences → Security & Privacy → Privacy → Network
   ```

### Linux Issues

1. **Missing Development Headers**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-dev python3-pip

   # CentOS/RHEL
   sudo yum install python3-devel python3-pip
   ```

2. **SELinux Issues**
   ```bash
   # Check SELinux status
   getenforce
   
   # Temporarily disable for testing
   sudo setenforce 0
   ```

---

## 🆘 Getting Help

### Information to Collect

When reporting issues, please provide:

1. **System Information**
   ```bash
   python --version
   pip list | grep -E "(requests|matplotlib|pandas)"
   uname -a  # Linux/Mac
   systeminfo | findstr /B /C:"OS Name" /C:"OS Version"  # Windows
   ```

2. **Error Messages**
   - Full error traceback
   - Screenshot of error (if GUI)
   - Log file contents

3. **Configuration**
   - Miner configuration (anonymize IPs if needed)
   - Network topology diagram
   - Bitaxe firmware versions

4. **Reproduction Steps**
   - Exact commands run
   - When the issue occurs
   - Any recent changes

### Test Scripts

**Network Connectivity Test:**
```python
#!/usr/bin/env python3
import requests
import socket

miners = [
    {'name': 'Test-1', 'ip': '192.168.1.45'}
]

for miner in miners:
    print(f"Testing {miner['name']} ({miner['ip']}):")
    
    # Ping test
    response = os.system(f"ping -c 1 {miner['ip']} >/dev/null 2>&1")
    print(f"  Ping: {'✅ OK' if response == 0 else '❌ Failed'}")
    
    # Port test
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((miner['ip'], 80))
        sock.close()
        print(f"  Port 80: {'✅ Open' if result == 0 else '❌ Closed'}")
    except Exception as e:
        print(f"  Port 80: ❌ Error - {e}")
    
    # API test
    try:
        r = requests.get(f"http://{miner['ip']}/api/system/info", timeout=5)
        print(f"  API: ✅ OK (Status: {r.status_code})")
        data = r.json()
        print(f"  Model: {data.get('ASICModel', 'Unknown')}")
        print(f"  Firmware: {data.get('version', 'Unknown')}")
    except Exception as e:
        print(f"  API: ❌ Error - {e}")
    
    print()
```

**CSV Analysis Script:**
```python
#!/usr/bin/env python3
import pandas as pd
import glob

csv_files = glob.glob("multi_bitaxe_kpis_*.csv")
if not csv_files:
    print("❌ No CSV files found")
    exit(1)

latest_file = max(csv_files, key=os.path.getctime)
print(f"📁 Analyzing: {latest_file}")

df = pd.read_csv(latest_file)
print(f"📊 Total rows: {len(df)}")
print(f"📊 Columns: {len(df.columns)}")
print(f"📊 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"📊 Miners: {', '.join(df['miner_name'].unique())}")
print(f"📊 Status distribution:\n{df['status'].value_counts()}")

online_data = df[df['status'] == 'ONLINE']
if len(online_data) > 0:
    print(f"✅ {len(online_data)} online data points found")
    print(f"📈 Hashrate range: {online_data['hashrate_th'].min():.3f} - {online_data['hashrate_th'].max():.3f} TH/s")
else:
    print("❌ No online data points found")
```

---

## 📞 Support Channels

- **GitHub Issues**: For bugs and feature requests
- **Community Forums**: For general questions and discussions
- **Documentation**: Check API reference and examples
- **Discord/Telegram**: Real-time community support (if available)

Remember to search existing issues before creating new ones!
