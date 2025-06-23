# Enhanced BitAxe Monitor

A comprehensive Python monitoring tool for multiple BitAxe miners with **real-time charts**, **console view**, and enhanced variance tracking.

![Enhanced BitAxe Monitor](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Enhanced Monitor](https://img.shields.io/badge/Enhanced%20Monitor-Working-brightgreen.svg)
![Console View](https://img.shields.io/badge/Console%20View-NEW-orange.svg)
![Charts](https://img.shields.io/badge/Charts-Beautiful-brightgreen.svg)

## 🎯 **Key Features**

### **🖥️ Console View - NEW!**
- **Terminal Interface**: Real-time console output with live fleet statistics
- **Clean Dashboard**: Color-coded status indicators and emoji icons
- **Live Updates**: 30-second refresh intervals with formatted miner details
- **Dual Mode**: Run console view alongside web interface

### **📊 Enhanced Real-time Charts**
- **4 Beautiful Charts per Miner**: Hashrate, Directional Variance, Efficiency, Power/Temperature
- **60-Minute Analytics**: Extended data retention (120 data points at 30s intervals)
- **Modern Styling**: Gradient backgrounds, smooth animations, professional color schemes
- **Responsive Design**: Optimized for desktop and mobile viewing

### **⚡ Performance Optimizations**
- **30-Second Polling**: Reduced from 5s to 30s for better system performance
- **Efficient Data Storage**: Ring buffers with 60-minute capacity
- **Smart Threading**: Background data collection with thread safety
- **Memory Optimized**: Automatic data point limits and cleanup

### **🎨 Beautiful Visual Design**
- **Modern UI**: Gradient backgrounds, glassmorphism effects, hover animations
- **Color-Coded Efficiency**: Green (≥95%), Orange (85-94%), Red (<85%)
- **Professional Charts**: Chart.js with custom styling, tooltips, and smooth curves
- **Enhanced Typography**: Clear, readable fonts with proper hierarchy

### **🔧 Production-Ready Features**
- **Dual Interface**: Console mode for servers, web mode for monitoring
- **Command Line Arguments**: `--console` for terminal mode, `--port` for custom ports
- **Error Handling**: Graceful offline miner handling with status indicators
- **Fleet Statistics**: Total hashrate, power consumption, efficiency tracking

## 🚀 **Quick Start**

### **1. Configure Your Miners**
Edit `enhanced_bitaxe_monitor.py` around line 700:
```python
miners_config = [
    {'name': 'BitAxe-Gamma-1', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200},
    {'name': 'BitAxe-Gamma-2', 'ip': '192.168.1.46', 'expected_hashrate_gh': 1150},
    {'name': 'BitAxe-Gamma-3', 'ip': '192.168.1.47', 'expected_hashrate_gh': 1100}
]
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Run the Monitor**

**Console Mode (NEW!):**
```bash
python enhanced_bitaxe_monitor.py --console
# OR
python enhanced_bitaxe_monitor.py -c
```

**Web Mode (Default):**
```bash
python enhanced_bitaxe_monitor.py
# Custom port
python enhanced_bitaxe_monitor.py --port 8090
```

### **4. Access Dashboard**
- **Web Interface**: `http://localhost:8080`
- **Console Interface**: Live terminal output with 30s updates

## 📊 **Chart Features**

### **📈 Real-time Hashrate Chart**
- Live GH/s performance tracking
- 60-minute data retention (120 data points)
- Beautiful gradient fills and smooth animations
- Blue gradient theme with professional styling

### **📊 Directional Variance Chart**
- **Red gradient theme**: Visual deviation from expected performance
- **Trend analysis**: Spot performance patterns over 60 minutes
- **Zero-line reference**: Clear baseline for variance visualization

### **⚡ Efficiency Tracking Chart**
- **Green gradient theme**: Percentage efficiency over time
- Y-axis optimized for realistic efficiency ranges
- Color-coded efficiency indicators

### **🔥 Power & Temperature Chart**
- **Orange gradient theme**: Combined power and temperature monitoring
- Dual-metric visualization
- Performance correlation insights

## 🖥️ **Console View Features**

### **Real-time Fleet Summary**
```
🚀 Enhanced BitAxe Monitor - Console View
📊 2025-06-23 14:30:15
================================================================================

📈 FLEET SUMMARY
   Total Hashrate: 3.450 TH/s
   Total Power:    45.2 W
   Fleet Efficiency: 104.5%
   Miners Online:  3/3

⚒️  MINER DETAILS
--------------------------------------------------------------------------------
Name                 Status   Hashrate     Efficiency   Power    Temp
--------------------------------------------------------------------------------
BitAxe-Gamma-1       🟢 ONLINE 1205.3 GH/s    ✅100.4%       15.1 W   65.2°C
BitAxe-Gamma-2       🟢 ONLINE 1156.8 GH/s    ✅100.6%       15.0 W   64.8°C
BitAxe-Gamma-3       🟢 ONLINE 1088.1 GH/s    ⚠️ 98.9%       15.1 W   66.1°C

🔄 Next update in 30 seconds... (Press Ctrl+C to stop)
```

### **Status Indicators**
- **🟢 Green Circle**: Miner online and functioning
- **🔴 Red Circle**: Miner offline or unreachable
- **✅ Green Checkmark**: Efficiency ≥95%
- **⚠️ Yellow Warning**: Efficiency 85-94%
- **❌ Red X**: Efficiency <85%

## 📈 **Performance Improvements**

### **Optimized Polling**
- **30-second intervals**: Reduced from 5s for better performance
- **60-minute data retention**: 120 data points maximum
- **Efficient memory usage**: Ring buffers with automatic cleanup
- **Thread-safe operations**: Background data collection

### **Enhanced Data Storage**
- **Chart data optimization**: Deque collections with fixed capacity
- **JSON serialization**: Proper handling for web API responses
- **Memory management**: Automatic old data pruning

## 🔗 **API Endpoints**

### **Enhanced Monitor API**
```
GET /                     # Enhanced dashboard with beautiful charts
GET /api/metrics          # JSON metrics for all miners
```

### **Response Format**
```json
{
  "timestamp": "2025-06-23T14:30:00.000000",
  "total_hashrate_th": 3.450,
  "total_power_w": 45.2,
  "fleet_efficiency": 104.5,
  "online_count": 3,
  "total_count": 3,
  "miners": [
    {
      "miner_name": "BitAxe-Gamma-1",
      "status": "ONLINE",
      "hashrate_gh": 1205.3,
      "expected_hashrate_gh": 1200,
      "hashrate_efficiency_pct": 100.4,
      "power_w": 15.1,
      "temperature_c": 65.2
    }
  ],
  "chart_data": {
    "BitAxe-Gamma-1": {
      "timestamps": ["14:29:30", "14:30:00"],
      "hashrates": [1205.3, 1203.8],
      "variances": [5.3, 3.8],
      "efficiencies": [100.4, 100.3],
      "power": [15.1, 15.1],
      "temperature": [65.2, 65.3]
    }
  }
}
```

## 🎯 **Usage Examples**

### **Server Deployment (Console Mode)**
```bash
# Perfect for headless servers or SSH sessions
python enhanced_bitaxe_monitor.py --console --port 8080
```

### **Desktop Monitoring (Web Mode)**
```bash
# Full web interface with beautiful charts
python enhanced_bitaxe_monitor.py
```

### **Custom Configuration**
```bash
# Console mode on custom port
python enhanced_bitaxe_monitor.py -c -p 9000
```

## 🛠️ **Troubleshooting**

### **Console View Issues**
- **Terminal encoding**: Ensure terminal supports UTF-8 for emoji icons
- **Screen clearing**: Works on Windows (cls) and Unix (clear)
- **Threading**: Console updates run in background thread

### **Charts Not Updating**
- **API connectivity**: Verify `/api/metrics` endpoint accessibility
- **30-second intervals**: Charts update every 30 seconds (not 5s)
- **Browser compatibility**: Requires modern browser with JavaScript enabled

### **Miners Show Offline**
- **Network connectivity**: Verify miner IP addresses in configuration
- **API endpoints**: Test direct access to `http://[miner-ip]/api/system/info`
- **Timeout settings**: 5-second timeout for miner API calls

## 📋 **Requirements**

- **Python**: 3.9+ (recommended: 3.11)
- **Dependencies**: Flask, Requests (see requirements.txt)
- **Network**: BitAxe miners accessible via HTTP
- **Terminal**: UTF-8 support for console mode emoji icons
- **Browser**: Modern browser with JavaScript for web interface

## 📁 **Project Structure**

```
bitaxe-monitor/
├── enhanced_bitaxe_monitor.py    # Main monitor application (741 lines)
├── requirements.txt              # Python dependencies
├── README.md                     # This documentation
├── license.txt                   # MIT license
└── .gitignore                    # Git ignore rules
```

## 🔄 **Version History**

### **v2.0 - Console View & Performance Update**
- ✅ **NEW**: Console view with terminal interface
- ✅ **NEW**: 30-second polling intervals (improved performance)
- ✅ **NEW**: 60-minute chart data retention
- ✅ **NEW**: Beautiful chart styling with gradients
- ✅ **NEW**: Command line arguments (--console, --port)
- ✅ **IMPROVED**: Threading architecture for dual interfaces
- ✅ **IMPROVED**: Memory optimization with ring buffers
- ✅ **IMPROVED**: Modern UI design with glassmorphism effects

### **v1.0 - Initial Release**
- ✅ Basic web interface with 4 charts per miner
- ✅ Real-time variance tracking and statistical analysis
- ✅ Fleet efficiency monitoring
- ✅ 5-second polling intervals

## 📄 **License**

MIT License - see [LICENSE](license.txt) for details.

---

**🚀 Ready to monitor your BitAxe fleet with console view, beautiful charts, and optimized performance!**

### **Quick Commands:**
```bash
# Console mode (recommended for servers)
python enhanced_bitaxe_monitor.py --console

# Web mode (recommended for desktop)
python enhanced_bitaxe_monitor.py

# Help
python enhanced_bitaxe_monitor.py --help
```
