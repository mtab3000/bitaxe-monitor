# Multi-Bitaxe Monitor

A comprehensive Python monitoring tool for multiple Bitaxe miners with real-time performance metrics, variance tracking, web dashboard, and Docker deployment support.

![Multi-Bitaxe Monitor](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Code Quality](https://github.com/mtab3000/bitaxe-monitor/workflows/Code%20Quality/badge.svg)

## 🔥 Features

### **Real-time Monitoring**
- Monitor multiple Bitaxe miners simultaneously
- 60-second polling intervals (configurable)
- Concurrent data collection for fast updates
- Web dashboard accessible from any device

### **📊 Enhanced Web Interface**
- **Responsive Design**: Desktop and mobile-optimized views
- **Real-time Charts**: Hashrate, efficiency, variance, and voltage over time
- **Persistent Charts**: Graphs never disappear or reset
- **Visual Alerts**: Background turns red when efficiency drops below 80%
- **Multi-Chart View**: All chart types visible simultaneously (stacked layout)
- **Interactive**: Toggle between desktop and mobile layouts

### **⚡ Comprehensive Metrics**
- Hashrate (actual vs expected) with efficiency calculation
- Power consumption and J/TH efficiency tracking
- Temperature monitoring (ASIC + VR)
- Voltage tracking (set, actual, input) with dedicated charts
- Fan speed and frequency monitoring
- Pool connection and share statistics
- **Variance Tracking**: Monitor hashrate stability over 60s, 300s, 600s windows

### **🐳 Docker Deployment**
- **Environment-based Configuration**: No hardcoded IPs
- **Persistent Data**: CSV data survives container restarts
- **Auto-restart**: Container recovery on failure
- **Health Checks**: Built-in monitoring
- **Interactive Setup**: Quick start scripts for easy deployment

### **📋 Smart Analytics**
- Expected hashrate calculation based on ASIC model and frequency
- Performance efficiency indicators with visual warnings
- Fleet-wide statistics and averages
- Historical data logging to single persistent CSV file
- Variance analysis with stability ratings (STABLE/MEDIUM/HIGH)

### **🎯 Supported Models**
- Bitaxe Gamma (BM1370) - 1.2 TH/s @ 600MHz
- Bitaxe Supra (BM1368) - 700 GH/s @ 650MHz  
- Bitaxe Ultra (BM1366) - 500 GH/s @ 525MHz
- Bitaxe Max (BM1397) - 400 GH/s @ 450MHz

### **🥧 Raspberry Pi Compatible**
- ASCII-only console output (no Unicode issues)
- Optimized for SSH/terminal access
- Low resource usage

## Installation

## Installation

### Prerequisites
- Python 3.8 or higher
- Network access to your Bitaxe miners

### Quick Start
```bash
# Clone the repository
git clone https://github.com/mtab3000/bitaxe-monitor.git
cd bitaxe-monitor

# Install dependencies
pip install -r requirements.txt

# Configure your miners (edit the script)
nano src/bitaxe_monitor.py

# Run the enhanced monitor
python src/bitaxe_monitor.py
```

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python tests/run_tests.py

# Run with pylint checks
pylint src/ --disable=C0114,C0115,C0116 --max-line-length=120
```

### 🐳 Docker Deployment

For easier deployment and management, you can run the enhanced monitor with Docker:

#### Prerequisites
- Docker and Docker Compose installed
- Network access to your Bitaxe miners

#### Quick Docker Start
```bash
# Clone the repository
git clone https://github.com/mtab3000/bitaxe-monitor.git
cd bitaxe-monitor

# Use the quick start script (Linux/Mac)
chmod +x docker-start.sh
./docker-start.sh

# OR edit docker-compose.yml manually with your miner IPs
nano docker-compose.yml

# Start the monitor
docker-compose up -d
```

**Windows Users**: Use `docker-start.bat` for an interactive setup experience.

#### Docker Configuration
Edit the environment variables in `docker-compose.yml`:

```yaml
environment:
  # Miner Configuration (comma-separated)
  - MINER_NAMES=Gamma-1,Gamma-2,Gamma-3
  - MINER_IPS=192.168.1.45,192.168.1.46,192.168.1.47
  - MINER_PORTS=80,80,80
  
  # Monitor Settings
  - POLL_INTERVAL=60
  - WEB_PORT=8080
  
  # Optional: Expected hashrates (format: name:rate,name:rate)
  - EXPECTED_HASHRATES=Gamma-1:1200,Gamma-2:1150
```

#### Docker Features
- 🌐 **Enhanced Web Interface**: Uses `bitaxe-monitor-variance-webserver.py` with full web dashboard
- 💾 **Persistent Data**: CSV data saved to `./data/` directory
- 🔄 **Auto-restart**: Container restarts automatically on failure
- 📊 **Advanced Charts**: Desktop and mobile-optimized views with variance tracking
- 🚨 **Alerts**: Visual efficiency warnings and background alerts
- 📱 **Mobile Support**: Responsive design for phone/tablet monitoring
- 🔒 **Persistent Charts**: Graphs never disappear or reset between updates

#### Docker Commands
```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the monitor
docker-compose down

# Update and restart
docker-compose pull && docker-compose up -d

# Access container shell
docker-compose exec bitaxe-monitor sh
```

#### Docker Web Interface Features
- **Real-time Charts**: Hashrate, efficiency, variance, and voltage over time
- **Mobile/Desktop Views**: Toggle between optimized layouts
- **Persistent Charts**: Graphs never disappear or reset
- **Efficiency Alerts**: Background turns red when efficiency drops below 80%
- **Variance Tracking**: Monitor hashrate stability across different time windows
- **Multi-Chart View**: All chart types visible simultaneously (stacked layout)

## Configuration

### Local Configuration
Edit the `miners_config` list in `src/bitaxe_monitor.py`:

```python
miners_config = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45'},
    {'name': 'Gamma-2', 'ip': '192.168.1.46'},
    {'name': 'Gamma-3', 'ip': '192.168.1.47', 'port': 8080},  # Custom port
]
```

### Docker Configuration (Recommended)
Configure via environment variables in `docker/docker-compose.yml`:

```yaml
environment:
  # Miner Configuration (comma-separated)
  - MINER_NAMES=Gamma-1,Gamma-2,Gamma-3
  - MINER_IPS=192.168.1.45,192.168.1.46,192.168.1.47
  - MINER_PORTS=80,80,80
  
  # Monitor Settings
  - POLL_INTERVAL=60
  - WEB_PORT=8080
  
  # Optional: Expected hashrates (format: name:rate,name:rate)
  - EXPECTED_HASHRATES=Gamma-1:1200,Gamma-2:1150
```

## Usage

### Basic Monitoring
```bash
# Local execution
python src/bitaxe_monitor.py

# Access web interface
open http://localhost:8080
```

### Example Console Output
```
>> Multi-Bitaxe Summary - 2025-06-22 14:29:38
===============================================================================
 Miner     Hash(TH)  Power  FREQ    SET V   ACT V   J/TH  Eff%   Temp   Fan    s60s   s300s  s600s  Variance  Uptime
 ON  Gamma-1   1.026    15W  503MHz  1.020V  1.001V  14.3  102!  60.12  4094   12.3   14.1   15.8   STABLE    2d 5h
 ON  Gamma-2   1.018    15W  503MHz  1.020V  0.988V  14.7  101!  60.12  3385   45.2!  48.1!  52.3!  HIGH!     1d 3h
 ON  Gamma-3   1.092    14W  506MHz  1.020V  0.998V  12.5  108!  59.75  2638   8.7    9.2    10.1   STABLE    3d 2h
===============================================================================
 SUM TOTALS   3.136    43W    ---     ---     ---    13.8  104!  60.00  3372

>> Legend: s = Standard Deviation (GH/s) | 60s/300s/600s windows
   ! = High value/warning | * = Good performance | STABLE/MEDIUM/HIGH = Variance rating
```

### Web Interface Features
- **Real-time Charts**: Auto-updating every 5 seconds
- **Mobile/Desktop Toggle**: Optimized layouts for different devices  
- **Efficiency Alerts**: Visual warnings when performance drops
- **Variance Analysis**: Monitor hashrate stability over time
- **Persistent Charts**: Never disappear or reset between updates

## Data Logging

The monitor automatically creates timestamped CSV files with comprehensive metrics:
- `multi_bitaxe_kpis_YYYYMMDD_HHMMSS.csv`

### CSV Columns
- Timestamps and miner identification
- Hashrate (actual, expected, efficiency %)
- Power metrics (watts, J/TH efficiency)
- Temperatures (ASIC, VR)
- Voltages (set, actual, input)
- Network and pool information
- Hardware details (ASIC model, firmware, etc.)

## API Endpoints Used

The monitor uses the following Bitaxe API endpoint:
- `GET /api/system/info` - Comprehensive system information

## Efficiency Calculation

Expected hashrate is calculated using:
```
Expected GH/s = Base Hashrate × (Current Frequency / Base Frequency)
```

Base specifications per ASIC:
- **BM1370**: 1200 GH/s @ 600MHz
- **BM1368**: 700 GH/s @ 650MHz
- **BM1366**: 500 GH/s @ 525MHz
- **BM1397**: 400 GH/s @ 450MHz

## Troubleshooting

### Connection Issues
- Verify miner IP addresses and network connectivity
- Check firewall settings
- Ensure miners are powered on and responding

### Performance Issues
- Monitor shows collection time warnings if polling takes >30 seconds
- Reduce number of concurrent miners if network is slow
- Check for network latency issues

### Display Issues
- Ensure terminal supports UTF-8 for emoji display
- Use `show_detailed=False` for cleaner output in simple terminals

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
```bash
git clone https://github.com/mtab3000/bitaxe-monitor.git
cd bitaxe-monitor
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for the Bitaxe open-source mining community
- Supports all Bitaxe hardware variants
- Inspired by the need for comprehensive fleet monitoring

## Related Projects

**🔗 Complete Bitaxe Toolkit:**
- **[Bitaxe-Hashrate-Benchmark](https://github.com/mtab3000/Bitaxe-Hashrate-Benchmark)** - Performance optimization and parallel benchmarking
- **[Bitaxe-Temp-Monitor](https://github.com/mtab3000/bitaxe-temp-monitor)** - Intelligent temperature-based auto-tuning
- **[AxeOS Firmware](https://github.com/bitaxeorg/axeOS)** - Bitaxe firmware
- **[Bitaxe Hardware](https://github.com/skot/bitaxe)** - Original Bitaxe project

## Workflow Integration

This monitoring tool works perfectly with other Bitaxe utilities:

1. **🔧 Optimize**: Use `Bitaxe-Hashrate-Benchmark` to find best settings
2. **📊 Monitor**: Use this tool for ongoing fleet oversight  
3. **🌡️ Automate**: Use `Bitaxe-Temp-Monitor` for hands-free operation

---

**Made with ❤️ for the Bitcoin mining community**