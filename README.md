# Bitaxe Monitor & Visualizer

A comprehensive Python toolkit for monitoring and analyzing multiple Bitaxe Gamma ASIC Bitcoin miners. This repository contains two complementary tools that work together to provide real-time monitoring, data logging, and advanced performance analysis.

## 🚀 Features

### 📊 Multi-Bitaxe Monitor (`bitaxe_monitor.py`)
- **Real-time monitoring** of multiple Bitaxe miners simultaneously
- **Comprehensive KPI tracking** - 20+ metrics per miner
- **Clean table display** with status indicators
- **CSV data logging** for historical analysis
- **Concurrent polling** using threading for fast updates
- **Error handling** with offline miner detection
- **60-second polling intervals** optimized for network efficiency

### 📈 CSV Visualizer (`bitaxe_visualizer.py`)
- **Professional matplotlib graphs** from logged CSV data
- **5 different visualization types** for comprehensive analysis
- **Individual miner trends** with statistical summaries
- **Multi-miner comparisons** on unified charts
- **Performance optimization recommendations** with exact settings
- **Efficiency analysis** with correlation studies
- **High-resolution output** (300 DPI PNG files)

## 📋 Monitored Metrics

### Core Performance
- **Hashrate** (GH/s and TH/s) - Mining performance
- **Power Consumption** (W) - Current power draw
- **Efficiency** (J/TH) - Power efficiency in Joules per Terahash

### Hardware Status  
- **ASIC Temperature** (°C) - Chip temperature
- **VR Temperature** (°C) - Voltage regulator temperature
- **Core Voltage** (V) - Actual ASIC core voltage
- **Input Voltage** (V) - Supply voltage
- **Frequency** (MHz) - ASIC clock frequency
- **Fan Speed** (RPM) - Cooling fan speed

### Mining Statistics
- **Best Difficulty** - Highest difficulty share found
- **Session Difficulty** - Best difficulty this session
- **Accepted/Rejected Shares** - Mining pool statistics
- **Pool Information** - URL and worker configuration

### System Information
- **Uptime** - Miner runtime in seconds
- **WiFi Signal** (dBm) - Network connection strength
- **Hardware Details** - ASIC model, board version, firmware

## 🛠️ Installation

### Prerequisites
- Python 3.6 or higher
- pip package manager

### Install Dependencies
```bash
# For monitoring only
pip install requests

# For visualization (includes monitoring dependencies)
pip install requests matplotlib pandas numpy
```

### Download Scripts
```bash
git clone https://github.com/yourusername/bitaxe-monitor-visualizer.git
cd bitaxe-monitor-visualizer
```

## ⚙️ Configuration

### 1. Configure Your Miners
Edit the `miners_config` list in both scripts:

```python
miners_config = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45'},
    {'name': 'Gamma-2', 'ip': '192.168.1.46'},
    {'name': 'Gamma-3', 'ip': '192.168.1.47'}
]
```

**Configuration Options:**
- `name` - Custom identifier for your miner
- `ip` - IP address of your Bitaxe miner
- `port` - Optional port number (defaults to 80)

### 2. Network Requirements
- All miners must be accessible on your local network
- Standard HTTP port 80 access required
- No authentication or special router configuration needed

## 🎯 Usage

### Step 1: Start Monitoring
```bash
# Basic monitoring with clean table display
python bitaxe_monitor.py

# With detailed individual miner information
python bitaxe_monitor.py  # Edit show_detailed=True in script
```

**Sample Monitor Output:**
```
🔥 Multi-Bitaxe Summary - 2025-05-29 18:38:49
=============================================================================================================================
Miner         Hashrate     Power      Efficiency     ASIC      VR    Core   Input     Freq       Fan
-----------------------------------------------------------------------------------------------------------------------------
🟢 Gamma-1      1.035 TH/s   19.7W   **19.04 J/TH**   59.9°C   57.0°C  1.133V    4.97V   570MHz     2981RPM
🟢 Gamma-2      1.425 TH/s   19.7W   **13.85 J/TH**   60.2°C   57.0°C  1.126V    5.07V   570MHz     3156RPM
🟢 Gamma-3      1.019 TH/s   17.3W   **17.00 J/TH**   56.6°C   53.0°C  1.131V    5.11V   570MHz     2157RPM
-----------------------------------------------------------------------------------------------------------------------------
📊 TOTALS       3.479 TH/s   56.8W   **16.32 J/TH**   3/3 miners online
```

### Step 2: Generate Visualizations
```bash
# Automatic CSV detection and all chart types
python bitaxe_visualizer.py

# Specify CSV file
python bitaxe_visualizer.py --csv multi_bitaxe_kpis_20250529_183849.csv

# Save charts without displaying
python bitaxe_visualizer.py --no-show

# Only individual miner trends
python bitaxe_visualizer.py --individual-only

# Only overview and analysis charts
python bitaxe_visualizer.py --overview-only
```

## 📊 Generated Visualizations

### 1. Individual Miner Trends
**Files:** `[MinerName]_performance_trends.png`
- Hashrate over time with average line
- Core voltage stability analysis  
- ASIC frequency trends
- Statistical summaries and time ranges

### 2. Multi-Miner Overview
**File:** `multi_bitaxe_overview.png`
- Side-by-side hashrate comparison
- Voltage regulation comparison
- Frequency scaling comparison
- Color-coded by miner for easy identification

### 3. Comprehensive Performance Analysis
**File:** `bitaxe_comprehensive_analysis.png`
- 9-panel dashboard with time series and correlations
- Power efficiency trends over time
- Temperature analysis (ASIC + VR)
- Fan speed response patterns
- Advanced correlation analysis

### 4. Hashrate Optimization
**File:** `bitaxe_hashrate_optimization.png`
- Optimal frequency settings for maximum hashrate
- Optimal voltage settings for peak performance
- Temperature impact on hashrate
- Exact settings summary with gold star highlights

### 5. Efficiency Optimization
**File:** `bitaxe_efficiency_optimization.png`
- Best frequency settings for maximum efficiency
- Optimal voltage for lowest J/TH
- Temperature vs efficiency correlation
- Settings recommendations for power optimization

## 🗂️ File Structure

```
bitaxe-monitor-visualizer/
├── bitaxe_monitor.py           # Real-time monitoring script
├── bitaxe_visualizer.py        # CSV data visualization script
├── README.md                   # This documentation
├── multi_bitaxe_kpis_*.csv     # Generated data files (timestamped)
└── generated_charts/
    ├── Gamma-1_performance_trends.png
    ├── Gamma-2_performance_trends.png  
    ├── Gamma-3_performance_trends.png
    ├── multi_bitaxe_overview.png
    ├── bitaxe_comprehensive_analysis.png
    ├── bitaxe_hashrate_optimization.png
    └── bitaxe_efficiency_optimization.png
```

## 📈 Data Analysis Workflow

### 1. **Data Collection Phase** (Monitor)
```bash
python bitaxe_monitor.py
# Let run for several hours/days to collect baseline data
# CSV files are automatically timestamped and saved
```

### 2. **Analysis Phase** (Visualizer)
```bash
python bitaxe_visualizer.py
# Generates all chart types from most recent CSV
# Provides optimization recommendations based on actual performance
```

### 3. **Optimization Phase** (Apply Settings)
- Review optimization charts for best settings
- Apply recommended frequency/voltage to miners via web interface
- Continue monitoring to verify improvements

### 4. **Continuous Monitoring**
- Run monitor continuously for ongoing data collection
- Generate new visualizations periodically to track changes
- Use trend analysis for predictive maintenance

## 🔧 Advanced Usage

### Custom Polling Intervals
Modify `time.sleep(60)` in the monitor script:
```python
time.sleep(30)   # Poll every 30 seconds
time.sleep(120)  # Poll every 2 minutes
```

### Adding More Miners
Simply extend the configuration list:
```python
miners_config = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45'},
    {'name': 'Gamma-2', 'ip': '192.168.1.46'},
    {'name': 'Gamma-3', 'ip': '192.168.1.47'},
    {'name': 'Gamma-4', 'ip': '192.168.1.48'},  # Add more miners
    {'name': 'Gamma-5', 'ip': '192.168.1.49'}
]
```

### Integration with Other Tools
CSV data can be imported into:
- **Excel/LibreOffice** for custom analysis
- **Grafana** for real-time dashboards
- **InfluxDB** for time-series storage
- **Custom Python scripts** for automated analysis

## 🚨 Troubleshooting

### Common Issues

**"Connection refused" or timeout errors:**
- Verify miner IP addresses are correct
- Ensure miners are powered on and connected to network
- Check that miners are accessible via web browser
- Verify firewall settings

**"No module named 'requests'" or similar:**
```bash
pip install requests matplotlib pandas numpy
```

**"No CSV files found":**
- Run the monitor script first to generate data
- Ensure you're in the correct directory
- Check that CSV files have the expected naming format

**Incorrect voltage readings:**
- Script uses `coreVoltageActual` for core voltage (~1.2V)
- Uses `voltage` field for input voltage (~12V)
- Values are automatically converted from mV to V

### Performance Optimization

**Memory Usage:**
- Monitor: Very low, only stores current readings
- Visualizer: Scales with CSV file size, typically under 100MB

**Network Impact:**
- One HTTP request per miner per polling interval
- Default 60-second intervals minimize network overhead
- Concurrent requests reduce total polling time

**Scalability:**
- Tested with 10+ miners simultaneously
- Linear scaling with number of miners
- No performance degradation observed

## 🤝 Contributing

We welcome contributions! Areas for improvement:

### Monitor Enhancements
- Additional Bitaxe API endpoints
- Database integration (SQLite, PostgreSQL)
- Web dashboard interface
- Alert/notification system
- Historical trend analysis

### Visualizer Enhancements
- Interactive plots with Plotly
- Real-time updating charts
- Machine learning performance predictions
- Custom chart configurations
- Export to different formats

### General Improvements
- Docker containerization
- Automated deployment scripts
- Unit tests and CI/CD
- Documentation improvements
- Performance optimizations

## 📊 Performance Notes

- **Monitor Resource Usage**: <1% CPU, <50MB RAM
- **Visualizer Processing**: Handles 10,000+ data points efficiently
- **Chart Generation**: ~5-10 seconds for all charts
- **Network Overhead**: Minimal, ~1KB per miner per poll
- **Storage**: ~1MB per day per miner for CSV data

## 🛡️ Security Considerations

- Scripts use **HTTP only** (standard Bitaxe API)
- **No authentication** required or stored
- **Local network access** only
- **No external data transmission**
- **Read-only operations** on miners

## 📜 License

This project is open source under the MIT License. Feel free to modify and distribute.

## 🙏 Acknowledgments

- **Bitaxe Team** for creating amazing open-source mining hardware
- **Community Contributors** for testing and feedback
- **Python Ecosystem** (matplotlib, pandas, requests) for excellent libraries

## 📞 Support

For issues and questions:

- **Script bugs**: Create an issue on GitHub
- **Bitaxe hardware**: Consult official Bitaxe documentation
- **Network connectivity**: Check your local network setup
- **Feature requests**: Open a GitHub discussion

---

**Happy Mining!** ⛏️💰

*Monitor your miners like a pro with comprehensive insights and optimization recommendations.*