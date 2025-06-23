# Enhanced BitAxe Monitor - Complete Quick Start Guide

## 🎯 What You Get
Your BitAxe monitor now includes **working real-time charts** with enhanced variance monitoring - exactly what you requested!

## 🚀 **FASTEST START** (2 minutes)

### 1. Configure Your Miners
Edit line 467 in `enhanced_bitaxe_monitor.py`:

```python
miners_config = [
    {'name': 'BitAxe-Gamma-1', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200},
    {'name': 'BitAxe-Gamma-2', 'ip': '192.168.1.46', 'expected_hashrate_gh': 1150},
    {'name': 'BitAxe-Gamma-3', 'ip': '192.168.1.47', 'expected_hashrate_gh': 1100}
]
```

**Replace with your actual miner IPs and expected hashrates.**

### 2. Install & Run
```bash
pip install flask requests
python enhanced_bitaxe_monitor.py
```

### 3. Open Browser
**http://localhost:8080**

**That's it!** You now have working real-time charts and enhanced variance monitoring.

---

## 📊 **Enhanced Features You'll See**

### ✅ **4 Real-time Charts Per Miner**
1. **Real-time Hashrate** - Live GH/s performance tracking
2. **Directional Variance** - Expected baseline (gray dashed) vs actual (blue)  
3. **Efficiency Tracking** - Percentage over time with color coding
4. **Variance Standard Deviation** - Multi-window stability analysis

### ✅ **Enhanced Variance Monitoring**
- **Multi-window analysis**: 60s, 300s, 600s time periods
- **Expected baseline tracking**: Visual comparison against targets
- **Directional variance**: See positive/negative deviations clearly
- **Real-time updates**: Charts refresh every 5 seconds

### ✅ **Professional Interface**
- **Fleet statistics**: Total hashrate, power, efficiency
- **Status indicators**: Online/offline with color coding
- **Responsive design**: Works on mobile and desktop
- **Auto-refresh**: Live data without manual refresh

---

## 🐳 **Docker Quick Start**

### Option A: Quick Docker Run
```bash
git clone https://github.com/mtab3000/bitaxe-monitor.git
cd bitaxe-monitor/docker
docker-compose up -d
```

### Option B: Custom Configuration
1. **Edit docker-compose.yml**:
```yaml
environment:
  - MINER_1_NAME=Your-Miner-Name
  - MINER_1_IP=192.168.1.XX
  - MINER_1_EXPECTED_HASHRATE=XXXX
```

2. **Start containers**:
```bash
docker-compose up -d
docker-compose logs -f
```

3. **Access dashboard**: http://localhost:8080

---

## 🔧 **Configuration Guide**

### **Finding Your Miner IPs**
```bash
# Scan your network for BitAxe miners
nmap -sn 192.168.1.0/24 | grep -B2 "Nmap scan report"

# Or check your router's device list
# Or use BitAxe discovery tools
```

### **Setting Expected Hashrates**
Based on your BitAxe model:
- **BM1366 (Supra)**: ~500-600 GH/s
- **BM1368 (Ultra)**: ~700-800 GH/s  
- **BM1370 (Gamma)**: ~1100-1300 GH/s
- **BM1397 (Alpha)**: ~400-500 GH/s

### **Configuration Examples**

#### **Single Miner**
```python
miners_config = [
    {'name': 'My-BitAxe', 'ip': '192.168.1.100', 'expected_hashrate_gh': 1200}
]
```

#### **Mixed Fleet**
```python
miners_config = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45', 'expected_hashrate_gh': 1200},
    {'name': 'Ultra-1', 'ip': '192.168.1.46', 'expected_hashrate_gh': 750},
    {'name': 'Supra-1', 'ip': '192.168.1.47', 'expected_hashrate_gh': 550}
]
```

#### **Large Fleet**
```python
miners_config = [
    {'name': f'Gamma-{i}', 'ip': f'192.168.1.{i+45}', 'expected_hashrate_gh': 1200}
    for i in range(10)  # Creates 10 miners: .45 through .54
]
```

---

## 📈 **Understanding the Charts**

### **Directional Variance Chart** (Key Feature!)
- **Gray dashed line**: Your expected hashrate baseline
- **Blue solid line**: Actual hashrate performance  
- **Above baseline**: Miner performing better than expected
- **Below baseline**: Miner underperforming
- **Trend analysis**: Spot performance patterns over time

### **Efficiency Color Coding**
- 🟢 **Green**: ≥95% efficiency (excellent performance)
- 🟡 **Orange**: 85-94% efficiency (good performance)
- 🔴 **Red**: <85% efficiency (needs attention)

### **Variance Metrics**
- **Std Dev (60s)**: Short-term stability (last minute)
- **Std Dev (300s)**: Medium-term stability (last 5 minutes)  
- **Std Dev (600s)**: Long-term stability (last 10 minutes)

**Lower standard deviation = more stable hashrate**

---

## 🛠️ **Troubleshooting**

### **Charts Not Showing**
```bash
# 1. Check if server is running
curl http://localhost:8080/api/metrics

# 2. Check browser console for JavaScript errors
# Press F12 in browser, check Console tab

# 3. Verify Chart.js loads
# Should see Chart.js in browser Network tab
```

### **Miners Show Offline**
```bash
# 1. Test direct API access
curl http://192.168.1.45/api/system/info

# 2. Check network connectivity
ping 192.168.1.45

# 3. Verify miner is powered and connected
# Check miner web interface directly
```

### **Port Already in Use**
```bash
# Find what's using port 8080
netstat -tlnp | grep 8080

# Kill conflicting process
sudo kill -9 <PID>

# Or use different port
# Edit enhanced_bitaxe_monitor.py line 476: port=8081
```

### **Permission Errors**
```bash
# Install dependencies with user flag
pip install --user flask requests

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install flask requests
```

---

## ⚡ **Performance Tips**

### **Faster Updates**
Edit line 405 in `enhanced_bitaxe_monitor.py`:
```javascript
setInterval(updateData, 3000);  // Update every 3 seconds instead of 5
```

### **More Chart History**
Edit line 358:
```javascript
const maxDataPoints = 30;  // Show 30 data points instead of 15
```

### **Reduce Resource Usage**
Edit line 405:
```javascript
setInterval(updateData, 10000);  // Update every 10 seconds
```

---

## 🎮 **Demo Mode** (Testing Without Miners)

Edit line 467 in `enhanced_bitaxe_monitor.py`:
```python
miners_config = [
    {'name': 'Demo-Gamma-1', 'ip': '127.0.0.1', 'expected_hashrate_gh': 1200},
    {'name': 'Demo-Gamma-2', 'ip': '127.0.0.2', 'expected_hashrate_gh': 1150},
    {'name': 'Demo-Gamma-3', 'ip': '127.0.0.3', 'expected_hashrate_gh': 1100}
]
```

This will show offline miners but test the interface.

---

## 🔒 **Production Deployment**

### **Reverse Proxy (nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **SSL/TLS Setup**
```bash
# With Let's Encrypt
certbot --nginx -d your-domain.com
```

### **Process Management (systemd)**
```bash
# Create service file: /etc/systemd/system/bitaxe-monitor.service
[Unit]
Description=Enhanced BitAxe Monitor
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/bitaxe-monitor
ExecStart=/usr/bin/python3 enhanced_bitaxe_monitor.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable bitaxe-monitor
sudo systemctl start bitaxe-monitor
```

---

## 📱 **Mobile Access**

The enhanced monitor is fully responsive:
- **Portrait mode**: Stacked layout for easy scrolling
- **Landscape mode**: Side-by-side charts
- **Touch friendly**: Large buttons and touch targets
- **Auto-scaling**: Charts resize to fit screen

---

## 🎯 **Common Use Cases**

### **Home Mining Operation**
- Monitor 1-5 BitAxe miners
- Track efficiency and temperature
- Get alerts when performance drops

### **Small Farm (5-20 miners)**
- Fleet overview dashboard
- Compare miner performance
- Identify underperforming units

### **Large Operation (20+ miners)**
- Use Docker for scalability
- Set up reverse proxy for remote access
- Implement monitoring alerts

---

## ✅ **Success Indicators**

You'll know everything is working when you see:
- ✅ All miners show "ONLINE" status
- ✅ Charts are updating every 5 seconds
- ✅ Gray baseline visible in directional variance charts
- ✅ Fleet statistics showing total hashrate
- ✅ Efficiency percentages with color coding

---

## 🎉 **You're Done!**

Your enhanced BitAxe monitor is now running with:
- ✅ Real-time Chart.js visualizations
- ✅ Enhanced variance monitoring  
- ✅ Directional baseline comparisons
- ✅ Multi-window variance analysis
- ✅ Professional responsive interface

**Enjoy monitoring your BitAxe fleet with the enhanced variance tracking you requested!**
