# Enhanced BitAxe Monitor

A simple, focused Python monitoring tool for multiple BitAxe miners with **real-time charts** and enhanced variance tracking.

![Enhanced BitAxe Monitor](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Enhanced Monitor](https://img.shields.io/badge/Enhanced%20Monitor-Working-brightgreen.svg)
![Charts](https://img.shields.io/badge/Charts-Functional-brightgreen.svg)

## 🎯 **Key Features**

### **📊 Real-time Charts with Chart.js**
- **4 Live Charts per Miner**: Hashrate, Directional Variance, Efficiency, Standard Deviation
- **Directional Variance Tracking**: Visual baseline (gray dashed line) vs actual performance (blue line)
- **Multi-window Analysis**: 60s, 300s, 600s variance windows
- **Auto-updating**: Charts refresh every 5 seconds with smooth animations
- **Professional Visualization**: Responsive design for desktop and mobile

### **⚡ Enhanced Variance Monitoring**
- **Expected Hashrate Baseline**: Configurable per-miner expected performance
- **Directional Analysis**: See positive/negative deviations from baseline
- **Statistical Tracking**: Standard deviation calculations across multiple time windows
- **Efficiency Color Coding**: Green (≥95%), Orange (85-94%), Red (<85%)
- **Fleet Statistics**: Total hashrate, power consumption, fleet efficiency

### **🔧 Production-Ready Architecture**
- **BitAxe API Integration**: Direct connection to `/api/system/info` endpoints
- **Error Handling**: Graceful offline miner handling with status indicators
- **Configurable Settings**: Easy miner IP and expected hashrate configuration
- **Professional Interface**: Modern web UI with responsive design

## 🚀 **Quick Start**

### **1. Configure Your Miners**
Edit `enhanced_bitaxe_monitor.py` around line 467:
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
```bash
python enhanced_bitaxe_monitor.py
```

### **4. Access Dashboard**
Open your browser to: `http://localhost:8080`

## 📊 **Chart Features**

### **Real-time Hashrate Chart**
- Live GH/s performance tracking
- Smooth line chart with fill gradient
- 15 data points visible (75 seconds of history)

### **Directional Variance Chart** ⭐ **KEY FEATURE**
- **Gray dashed line**: Expected hashrate baseline
- **Blue solid line**: Actual hashrate performance
- **Visual variance**: Instantly see over/under performance
- **Trend analysis**: Spot performance patterns over time

### **Efficiency Tracking Chart**
- Percentage efficiency over time
- Y-axis optimized for 85-115% range
- Color-coded values (green/orange/red)

### **Variance Standard Deviation Chart**
- Statistical variance analysis
- Multiple time windows (60s/300s/600s)
- Stability indicator for hashrate consistency

## 📈 **Monitored Metrics**

### **Per Miner**
- Hashrate (actual vs expected) with efficiency calculation
- Power consumption tracking
- Temperature monitoring
- Frequency and voltage readings
- Uptime statistics

### **Fleet Overview**
- Total hashrate across all miners
- Combined power consumption
- Fleet efficiency percentage
- Online/offline miner count

## 🔗 **API Endpoints**

### **Enhanced Monitor API**
```
GET /                     # Enhanced dashboard with charts
GET /api/metrics          # JSON metrics for all miners
```

### **Response Format**
```json
{
  "timestamp": "2025-06-23T10:30:00.000000",
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
      "hashrate_stddev_60s": 15.2,
      "hashrate_stddev_300s": 12.8,
      "hashrate_stddev_600s": 14.1,
      "power_w": 15.1,
      "temperature_c": 65.2
    }
  ]
}
```

## 🎯 **Troubleshooting**

### **Charts Not Showing**
- Ensure Chart.js loads (check browser console)
- Verify API endpoint: `http://localhost:8080/api/metrics`
- Check JavaScript is enabled in browser

### **Miners Show Offline**
- Verify miner IP addresses in configuration
- Ensure miners are powered and connected
- Test API directly: `http://[miner-ip]/api/system/info`

## 📋 **Requirements**

- **Python**: 3.9+ (recommended: 3.11)
- **Dependencies**: Flask, Requests (see requirements.txt)
- **Network**: BitAxe miners accessible via HTTP
- **Browser**: Modern browser with JavaScript enabled

## 📁 **Project Structure**

```
bitaxe-monitor/
├── enhanced_bitaxe_monitor.py    # Main monitor application
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── license.txt                   # MIT license
└── .gitignore                    # Git ignore rules
```

## 📄 **License**

MIT License - see [LICENSE](license.txt) for details.

---

**🚀 Ready to monitor your BitAxe fleet with enhanced variance tracking and real-time charts!**
