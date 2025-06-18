# Setup Guide

Complete setup instructions for different operating systems.

## Quick Start

1. **Download/Clone Repository**
   ```bash
   git clone https://github.com/mtab3000/bitaxe-monitor.git
   cd bitaxe-monitor
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Your Miners**
   Edit the `miners_config` list in `bitaxe_monitor_refactored.py`

4. **Run Monitor**
   ```bash
   python bitaxe_monitor_refactored.py
   ```

## Detailed Setup Instructions

### Windows

1. **Install Python 3.6+**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **Open Command Prompt**
   - Press `Win + R`, type `cmd`, press Enter

3. **Navigate to Project Directory**
   ```cmd
   cd C:\path\to\bitaxe-monitor
   ```

4. **Install Dependencies**
   ```cmd
   pip install requests
   ```

5. **Configure Miners**
   - Open `bitaxe_monitor_refactored.py` in Notepad
   - Update the `miners_config` section with your miner IPs

6. **Run Monitor**
   ```cmd
   python bitaxe_monitor_refactored.py
   ```

### Linux/macOS

1. **Install Python 3.6+**
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install python3 python3-pip
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip
   
   # macOS (with Homebrew)
   brew install python3
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/mtab3000/bitaxe-monitor.git
   cd bitaxe-monitor
   ```

3. **Install Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Make Install Script Executable (Optional)**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

5. **Configure and Run**
   ```bash
   # Edit configuration
   nano bitaxe_monitor_refactored.py
   
   # Run monitor
   python3 bitaxe_monitor_refactored.py
   ```

## Configuration Examples

### Basic Configuration
```python
miners_config = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45'},
    {'name': 'Gamma-2', 'ip': '192.168.1.46'},
]
```

### Advanced Configuration
```python
miners_config = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45', 'port': 80},
    {'name': 'Ultra-1', 'ip': '192.168.1.100', 'port': 8080},
    {'name': 'Max-1', 'ip': '10.0.1.50'},
]

# Optional: Override expected hashrates
expected_hashrates = {
    'Gamma-1': 1150,  # Custom expected hashrate
    'Ultra-1': 480,   # Underclocked Ultra
}
```

## Network Setup

### Find Your Miner IP Addresses

1. **Check Router Admin Panel**
   - Usually at `192.168.1.1` or `192.168.0.1`
   - Look for "Connected Devices" or "DHCP Clients"
   - Find devices named "bitaxe" or similar

2. **Use Network Scanner**
   ```bash
   # Linux/macOS
   nmap -sn 192.168.1.0/24
   
   # Windows (with nmap installed)
   nmap -sn 192.168.1.0/24
   ```

3. **Check Bitaxe Display** (if equipped)
   - IP address usually shown on OLED display

### Test Connection
```bash
# Test if miner is responding
curl http://192.168.1.45/api/system/info

# Should return JSON with miner information
```

## Troubleshooting

### Common Issues

1. **"Module not found" Error**
   ```bash
   pip install requests
   ```

2. **"Connection refused" Error**
   - Check miner IP address
   - Verify miner is powered on
   - Test network connectivity: `ping 192.168.1.45`

3. **"Permission denied" Error (Linux/macOS)**
   ```bash
   chmod +x bitaxe_monitor_refactored.py
   python3 bitaxe_monitor_refactored.py
   ```

4. **Emoji Display Issues**
   - Use a modern terminal (Windows Terminal, iTerm2, etc.)
   - Set terminal encoding to UTF-8

### Performance Tips

- **Fast Networks**: Monitor up to 10-15 miners simultaneously
- **Slow Networks**: Reduce miners or increase poll interval
- **Raspberry Pi**: Works great for dedicated monitoring

## Running as a Service

### Linux (systemd)

1. **Create Service File**
   ```bash
   sudo nano /etc/systemd/system/bitaxe-monitor.service
   ```

2. **Add Service Configuration**
   ```ini
   [Unit]
   Description=Bitaxe Monitor
   After=network.target
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/bitaxe-monitor
   ExecStart=/usr/bin/python3 bitaxe_monitor_refactored.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and Start**
   ```bash
   sudo systemctl enable bitaxe-monitor
   sudo systemctl start bitaxe-monitor
   ```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "At startup"
4. Set action to start `python.exe` with script path
5. Configure to run whether user is logged in or not

## Advanced Usage

### Custom Polling Interval
```python
monitor = MultiBitaxeMonitor(
    miners_config=miners_config,
    poll_interval=60  # 60 seconds instead of 30
)
```

### Enable Detailed View
```python
monitor.run_monitor(show_detailed=True)
```

### CSV Analysis
```python
import pandas as pd

# Load CSV data
df = pd.read_csv('multi_bitaxe_kpis_20250618_140238.csv')

# Calculate average efficiency per miner
avg_eff = df.groupby('miner_name')['hashrate_efficiency_pct'].mean()
print(avg_eff)
```

## Support

- **GitHub Issues**: [Create an issue](https://github.com/mtab3000/bitaxe-monitor/issues)
- **Bitaxe Community**: Join the Bitaxe Discord/Telegram
- **Documentation**: Check README.md for full details