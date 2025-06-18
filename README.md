# Multi-Bitaxe Monitor

A comprehensive Python monitoring tool for multiple Bitaxe miners that displays real-time performance metrics, calculates efficiency, and logs data to CSV.

![Multi-Bitaxe Monitor](https://img.shields.io/badge/Python-3.6+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

🔥 **Real-time Monitoring**
- Monitor multiple Bitaxe miners simultaneously
- 30-second polling intervals
- Concurrent data collection for fast updates

⚡ **Comprehensive Metrics**
- Hashrate (actual vs expected) with efficiency calculation
- Power consumption and J/TH efficiency
- Temperature monitoring (ASIC + VR)
- Voltage tracking (set, actual, input)
- Fan speed and frequency monitoring
- Pool connection and share statistics

📊 **Smart Analytics**
- Expected hashrate calculation based on ASIC model and frequency
- Performance efficiency indicators (🔥 ≥95%, ⚡ ≥85%, ⚠️ <70%)
- Fleet-wide statistics and averages
- Historical data logging to CSV

🎯 **Supported Models**
- Bitaxe Gamma (BM1370) - 1.2 TH/s @ 600MHz
- Bitaxe Supra (BM1368) - 700 GH/s @ 650MHz  
- Bitaxe Ultra (BM1366) - 500 GH/s @ 525MHz
- Bitaxe Max (BM1397) - 400 GH/s @ 450MHz

## Installation

### Prerequisites
- Python 3.6 or higher
- Network access to your Bitaxe miners

### Quick Start
```bash
# Clone the repository
git clone https://github.com/mtab3000/bitaxe-monitor.git
cd bitaxe-monitor

# Install dependencies
pip install -r requirements.txt

# Configure your miners (edit the script)
nano bitaxe_monitor_refactored.py

# Run the monitor
python bitaxe_monitor_refactored.py
```

## Configuration

Edit the `miners_config` list in `bitaxe_monitor_refactored.py`:

```python
miners_config = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45'},
    {'name': 'Gamma-2', 'ip': '192.168.1.46'},
    {'name': 'Gamma-3', 'ip': '192.168.1.47', 'port': 8080},  # Custom port
]
```

### Optional: Manual Expected Hashrate Override
```python
expected_hashrates = {
    'Gamma-1': 1200,  # Force expected hashrate to 1200 GH/s
    'Gamma-2': 1150,  # Custom target for specific miner
}
```

## Usage

### Basic Monitoring
```bash
python bitaxe_monitor_refactored.py
```

### With Detailed View
Edit the script and set `show_detailed=True` for individual miner details.

### Example Output
```
🔥 Multi-Bitaxe Summary - 2025-06-18 14:29:38
=====================================================================================
 Miner     Hash(TH)  Power  FREQ    SET V   J/TH  Eff%   Temp   Fan
---------------------------------------------------------------------------
 🟢 Gamma-1   1.026    15W  503MHz  1.020V  14.3  102🔥  60.12  4094
 🟢 Gamma-2   1.018    15W  503MHz  1.020V  14.7  101🔥  60.12  3385
 🟢 Gamma-3   1.092    14W  506MHz  1.020V  12.5  108🔥  59.75  2638
---------------------------------------------------------------------------
 📊 TOTALS   3.136    43W    ---     ---    13.8  104🔥  60.00  3372
=====================================================================================

📊 Additional Info:
   Gamma-1: VR:52.0°C  ActV:1.001V  InV:5.14V  Pool:taborsky.de
   Gamma-2: VR:52.0°C  ActV:0.988V  InV:5.10V  Pool:taborsky.de
   Gamma-3: VR:54.0°C  ActV:0.998V  InV:5.15V  Pool:taborsky.de

💡 Expected hashrate from BM1370 specs + frequency
```

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

- [Bitaxe Hardware](https://github.com/skot/bitaxe) - Original Bitaxe project
- [AxeOS Firmware](https://github.com/bitaxeorg/axeOS) - Bitaxe firmware

---

**Made with ❤️ for the Bitcoin mining community**