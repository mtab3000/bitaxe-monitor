# Enhanced BitAxe Monitor

A comprehensive Python monitoring tool for multiple BitAxe miners with **real-time charts**, enhanced variance tracking, professional web dashboard, and Docker deployment support.

![Enhanced BitAxe Monitor](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Enhanced Monitor](https://img.shields.io/badge/Enhanced%20Monitor-Working-brightgreen.svg)
![Charts](https://img.shields.io/badge/Charts-Functional-brightgreen.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

## 🎯 **ENHANCED FEATURES - NEW!**

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
- **Persistent Tracking**: Variance data maintained across updates
- **Professional Interface**: Modern web UI with responsive design

## 🚀 **Quick Start**

### **Option 1: Enhanced Monitor (Recommended)**
```bash
# 1. Configure your miners (edit enhanced_bitaxe_monitor.py line 467)
miners_config = [
    {'name': 'BitAxe-Gamma-1', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200},
    {'name': 'BitAxe-Gamma-2', 'ip': '192.168.1.46', 'expected_hashrate_gh': 1150},
    {'name': 'BitAxe-Gamma-3', 'ip': '192.168.1.47', 'expected_hashrate_gh': 1100}
]

# 2. Install dependencies
pip install flask requests

# 3. Run enhanced monitor  
python enhanced_bitaxe_monitor.py

# 4. Open browser
http://localhost:8080
```

### **Option 2: Docker Deployment**
```bash
# Clone repository
git clone https://github.com/mtab3000/bitaxe-monitor.git
cd bitaxe-monitor

# Configure miners in docker-compose.yml (already set to .45, .46, .47)
# Start enhanced monitor
cd docker
docker-compose up -d

# Monitor logs
docker-compose logs -f

# Access dashboard
http://localhost:8080
```

## 📊 **Enhanced Chart Features**

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

## 🔧 **Configuration**

### **Miner Configuration**
Edit `enhanced_bitaxe_monitor.py` at line 467:
```python
miners_config = [
    {'name': 'Your-Miner-Name', 'ip': '192.168.1.XX', 'expected_hashrate_gh': XXXX},
    # Add more miners as needed
]
```

### **Docker Environment Variables**
```yaml
environment:
  - MINER_1_NAME=BitAxe-Gamma-1
  - MINER_1_IP=192.168.1.45
  - MINER_1_EXPECTED_HASHRATE=1200
  # Configure additional miners...
```

## 📈 **Classic Features**

### **Comprehensive Metrics**
- Hashrate (actual vs expected) with efficiency calculation
- Power consumption and J/TH efficiency tracking  
- Temperature monitoring (ASIC + VR)
- Voltage tracking (set, actual, input)
- Fan speed and frequency monitoring
- Pool connection and share statistics

### **Smart Analytics**
- Expected hashrate calculation based on ASIC model and frequency
- Efficiency scoring with visual alerts
- Historic performance tracking
- Multi-miner fleet management

### **Web Dashboard**
- **Real-time Updates**: Auto-refresh every 5 seconds
- **Mobile Responsive**: Works on phones and tablets
- **Professional Design**: Clean, modern interface
- **Status Indicators**: Visual online/offline status
- **Fleet Overview**: Summary statistics for all miners

## 🐳 **Docker Features**

### **Environment-based Configuration**
- No hardcoded IPs in container
- Flexible miner configuration via environment variables
- Persistent data storage with named volumes

### **Production Ready**
- Health checks and auto-restart
- Resource limits and logging configuration
- Network isolation and security
- Container orchestration with docker-compose

## 📁 **Project Structure**

```
bitaxe-monitor/
├── enhanced_bitaxe_monitor.py    # 🆕 Enhanced monitor with charts
├── config.py                     # Configuration template
├── QUICK_START_GUIDE.md          # Setup instructions
├── src/                          # Original source code
├── docker/                       # Docker deployment
├── tests/                        # Test files
├── examples/                     # Configuration examples
├── docs/                         # Documentation
└── .github/workflows/            # CI/CD workflows
```

## 🧪 **Testing**

```bash
# Test enhanced monitor configuration
python test_config.py

# Run full test suite
pytest tests/ -v

# Test Docker build
cd docker && docker build -t bitaxe-monitor:test .
```

## 🏆 **Enhanced vs Classic**

| Feature | Classic Monitor | Enhanced Monitor |
|---------|----------------|------------------|
| **Charts** | ❌ Static data only | ✅ **Real-time Chart.js** |
| **Variance Tracking** | ❌ Basic | ✅ **Multi-window + Directional** |
| **Baseline Comparison** | ❌ No | ✅ **Expected vs Actual** |
| **Visual Interface** | ❌ Basic HTML | ✅ **Professional Dashboard** |
| **API Integration** | ✅ Yes | ✅ **Enhanced** |
| **Docker Support** | ✅ Yes | ✅ **Improved** |

## 📋 **Requirements**

- **Python**: 3.9+ (recommended: 3.11)
- **Dependencies**: Flask, Requests
- **Network**: BitAxe miners accessible via HTTP
- **Browser**: Modern browser with JavaScript enabled
- **Docker**: Optional, for containerized deployment

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

### **Docker Issues**
- Check environment variables in docker-compose.yml
- Verify port 8080 is not in use: `netstat -tlnp | grep 8080`
- Check container logs: `docker-compose logs -f`

## 🛡️ **Security**

- **Input Validation**: All user inputs sanitized
- **CORS Protection**: Secure API endpoints
- **Container Security**: Non-root user, minimal attack surface
- **Network Isolation**: Docker networking for secure deployment

## 📄 **License**

MIT License - see [LICENSE](license.txt) for details.

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 🎉 **Acknowledgments**

- BitAxe community for the excellent mining hardware
- Chart.js for beautiful real-time visualizations
- Flask community for the robust web framework
- Contributors who helped improve the monitoring capabilities

---

**🚀 Ready to monitor your BitAxe fleet with enhanced variance tracking and real-time charts!**
