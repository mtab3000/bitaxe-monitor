# API Reference Documentation

This document provides detailed information about the Bitaxe HTTP API and the functions available in the monitor and visualizer scripts.

## 🔌 Bitaxe HTTP API Reference

### Base URL Structure
```
http://{miner_ip}:{port}/api/{endpoint}
```

Default port: `80`

### Authentication
- **No authentication required**
- **HTTP only** (no HTTPS)
- **Local network access** typically required

---

## 📊 API Endpoints

### GET /api/system/info

Returns comprehensive system information including all monitored metrics.

**Request:**
```http
GET http://192.168.1.45/api/system/info
```

**Response Format:**
```json
{
    "power": 58.35,
    "voltage": 11906.25,
    "current": 16281.25,
    "temp": 58.0,
    "vrTemp": 45,
    "maxPower": 40,
    "nominalVoltage": 12,
    "hashRate": 2372.75,
    "bestDiff": "4.29G",
    "bestNonceDiff": 4292734826,
    "bestSessionDiff": "3.83M",
    "bestSessionNonceDiff": 3828108,
    "stratumDiff": 1000,
    "isUsingFallbackStratum": 0,
    "isPSRAMAvailable": 1,
    "freeHeap": 178368,
    "coreVoltage": 1200,
    "coreVoltageActual": 1194,
    "frequency": 525,
    "ssid": "NetworkName",
    "macAddr": "C0-FA-38-6A-6E-B2",
    "hostname": "bitaxe",
    "wifiStatus": "Connected!",
    "wifiRSSI": -44,
    "apEnabled": 0,
    "sharesAccepted": 19739,
    "sharesRejected": 6,
    "sharesRejectedReasons": [
        {
            "message": "Above target",
            "count": 6
        }
    ],
    "uptimeSeconds": 212115,
    "asicCount": 1,
    "smallCoreCount": 894,
    "ASICModel": "BM1366",
    "stratumURL": "public-pool.io",
    "fallbackStratumURL": "solo.ckpool.org",
    "stratumPort": 21496,
    "fallbackStratumPort": 3333,
    "stratumUser": "bc1qnp980s5fpp8l94p5cvttmtdqy8rvrq74qly2yrfmzkdsntqzlc5qkc4rkq.bitaxe",
    "fallbackStratumUser": "bc1qnp980s5fpp8l94p5cvttmtdqy8rvrq74qly2yrfmzkdsntqzlc5qkc4rkq.bitaxe",
    "version": "v2.6.0",
    "idfVersion": "v5.4",
    "boardVersion": "302",
    "runningPartition": "factory",
    "flipscreen": 1,
    "overheat_mode": 0,
    "overclockEnabled": 0,
    "invertscreen": 0,
    "invertfanpolarity": 1,
    "autofanspeed": 0,
    "fanspeed": 35,
    "fanrpm": 5515
}
```

### POST /api/system/restart

Restarts the Bitaxe miner.

**Request:**
```http
POST http://192.168.1.45/api/system/restart
```

**Response:**
```json
{
    "status": "restarting"
}
```

### PATCH /api/system

Updates system settings (requires restart for some settings).

**Request Example - Change Fan Speed:**
```http
PATCH http://192.168.1.45/api/system
Content-Type: application/json

{
    "fanspeed": 50
}
```

**Supported PATCH Parameters:**
- `fanspeed` - Fan speed percentage (0-100)
- `frequency` - ASIC frequency in MHz
- `coreVoltage` - Core voltage in mV
- `flipscreen` - Flip display (0/1)
- `invertscreen` - Invert display colors (0/1)

---

## 🐍 Python API Reference

## MultiBitaxeMonitor Class

### Constructor
```python
MultiBitaxeMonitor(miners_config)
```

**Parameters:**
- `miners_config` (list): List of miner configurations

**Example:**
```python
config = [
    {'name': 'Gamma-1', 'ip': '192.168.1.45'},
    {'name': 'Gamma-2', 'ip': '192.168.1.46', 'port': 8080}
]
monitor = MultiBitaxeMonitor(config)
```

### Methods

#### get_bitaxe_data(miner)
Retrieves data from a single miner's API.

**Parameters:**
- `miner` (dict): Miner configuration dictionary

**Returns:**
- `dict`: JSON response from API, or `None` on error

**Example:**
```python
miner_config = {'name': 'Gamma-1', 'ip': '192.168.1.45'}
data = monitor.get_bitaxe_data(miner_config)
if data:
    print(f"Hashrate: {data['hashRate']} H/s")
```

#### collect_miner_kpis(miner)
Processes raw API data into standardized KPI format.

**Parameters:**
- `miner` (dict): Miner configuration

**Returns:**
- `dict`: Processed KPI data

**KPI Data Structure:**
```python
{
    'timestamp': '2025-05-29T18:38:49.123456',
    'miner_name': 'Gamma-1',
    'miner_ip': '192.168.1.45',
    'status': 'ONLINE',
    'hashrate_gh': 1496.68,      # GH/s
    'hashrate_th': 1.497,        # TH/s  
    'power_w': 21.9,             # Watts
    'efficiency_jth': 14.63,     # J/TH
    'temperature_c': 59.9,       # Celsius
    'vr_temperature_c': 57.0,    # VR temp in Celsius
    'fan_speed_rpm': 2981,       # RPM
    'voltage_v': 1.133,          # Core voltage in V
    'input_voltage_v': 4.97,     # Input voltage in V
    'frequency_mhz': 570,        # MHz
    'best_diff': 4292734826,     # Best difficulty
    'session_diff': 3828108,     # Session difficulty
    'accepted_shares': 19739,    # Accepted shares
    'rejected_shares': 6,        # Rejected shares
    'uptime_s': 212115,          # Uptime in seconds
    'wifi_rssi': -44,            # WiFi signal dBm
    'pool_url': 'public-pool.io',
    'worker_name': 'bc1q...bitaxe',
    'asic_model': 'BM1366',
    'board_version': '302',
    'firmware_version': 'v2.6.0'
}
```

#### collect_all_kpis()
Collects KPIs from all miners concurrently.

**Returns:**
- `list`: List of KPI dictionaries sorted by miner name

#### display_summary(all_kpis)
Displays formatted summary table of all miners.

**Parameters:**
- `all_kpis` (list): List of KPI dictionaries

#### log_to_csv(all_kpis)
Logs KPI data to timestamped CSV file.

**Parameters:**
- `all_kpis` (list): List of KPI dictionaries

#### run_monitor(show_detailed=False)
Main monitoring loop with 60-second intervals.

**Parameters:**
- `show_detailed` (bool): Show individual miner details

---

## BitaxeVisualizer Class

### Constructor
```python
BitaxeVisualizer(csv_file_path)
```

**Parameters:**
- `csv_file_path` (str): Path to CSV file generated by monitor

### Methods

#### load_data()
Loads and preprocesses CSV data.

**Returns:**
- `bool`: True if successful, False otherwise

**Data Processing:**
- Converts timestamp strings to datetime objects
- Filters for online miners only
- Identifies unique miner names

#### create_miner_graphs(save_plots=True, show_plots=True)
Generates individual performance trend graphs for each miner.

**Parameters:**
- `save_plots` (bool): Save PNG files
- `show_plots` (bool): Display plots on screen

**Generated Files:**
- `{miner_name}_performance_trends.png`

#### create_combined_overview(save_plots=True, show_plots=True)  
Creates multi-miner comparison graphs.

**Generated Files:**
- `multi_bitaxe_overview.png`

#### create_efficiency_analysis(save_plots=True, show_plots=True)
Generates comprehensive 9-panel analysis dashboard.

**Generated Files:**
- `bitaxe_comprehensive_analysis.png`

#### create_optimization_charts(save_plots=True, show_plots=True)
Creates optimization recommendation charts.

**Generated Files:**
- `bitaxe_hashrate_optimization.png`
- `bitaxe_efficiency_optimization.png`

---

## 📊 Data Structures

### CSV File Format

**Columns:**
```
timestamp,miner_name,miner_ip,hashrate_gh,hashrate_th,power_w,efficiency_jth,
temperature_c,vr_temperature_c,fan_speed_rpm,voltage_v,input_voltage_v,
frequency_mhz,best_diff,session_diff,accepted_shares,rejected_shares,
uptime_s,wifi_rssi,pool_url,worker_name,asic_model,board_version,
firmware_version,status
```

**Sample Data:**
```csv
2025-05-29T18:38:49.123456,Gamma-1,192.168.1.45,1496.68,1.497,21.9,14.63,59.9,57.0,2981,1.133,4.97,570,4292734826,3828108,19739,6,212115,-44,public-pool.io,bc1q...bitaxe,BM1366,302,v2.6.0,ONLINE
```

### Status Values
- `ONLINE` - Miner responding normally
- `OFFLINE` - Network/connection error
- `ERROR` - Exception during data collection

---

## 🔧 Utility Functions

### find_latest_csv()
Automatically finds the most recent CSV file in current directory.

**Returns:**
- `str`: Path to latest CSV file, or `None` if not found

**Usage:**
```python
latest_file = find_latest_csv()
if latest_file:
    visualizer = BitaxeVisualizer(latest_file)
```

### Command Line Arguments

#### Monitor Script
```bash
python bitaxe_monitor.py
```

**Configuration:**
- Edit `miners_config` directly in script
- Modify `show_detailed` parameter for verbose output

#### Visualizer Script  
```bash
python bitaxe_visualizer.py [OPTIONS]
```

**Options:**
- `--csv, -f FILE` - Specify CSV file path
- `--no-show` - Don't display plots on screen  
- `--no-save` - Don't save plot files
- `--individual-only` - Only create individual miner graphs
- `--overview-only` - Only create overview graphs

---

## 🔄 API Data Conversions

### Unit Conversions Performed

| API Field | API Unit | Converted Unit | Conversion |
|-----------|----------|----------------|------------|
| `hashRate` | GH/s | TH/s | ÷ 1000 |
| `voltage` | mV | V | ÷ 1000 |
| `coreVoltageActual` | mV | V | ÷ 1000 |
| `temp` | °C | °C | No conversion |
| `vrTemp` | °C | °C | No conversion |
| `power` | W | W | No conversion |
| `fanrpm` | RPM | RPM | No conversion |
| `frequency` | MHz | MHz | No conversion |

### Calculated Fields

#### Efficiency (J/TH)
```python
efficiency_jth = power_w / hashrate_th
```

#### Hashrate Conversion
```python
hashrate_th = hashrate_gh / 1000  # GH/s to TH/s
```

---

## 🚨 Error Handling

### Network Errors
- **Connection timeout** (5 seconds)
- **HTTP errors** (404, 500, etc.)
- **JSON parsing errors**
- **Network unreachable**

### Data Validation
- **Missing required fields**
- **Invalid data types**  
- **Out-of-range values**
- **Timestamp parsing errors**

### File Operations
- **CSV write permissions**
- **Disk space availability**
- **File path validation**
- **PNG save errors**

---

## 🔍 Debugging

### Enable Debug Logging
Add to script:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### API Response Debugging  
```python
# Add to get_bitaxe_data method
print(f"Raw API response: {response.text}")
```

### CSV Data Debugging
```python
# Add to load_data method  
print(f"Loaded columns: {self.data.columns.tolist()}")
print(f"Data shape: {self.data.shape}")
print(f"Sample data:\n{self.data.head()}")
```

---

## 📈 Performance Considerations

### Memory Usage
- **Monitor**: ~50MB for 10 miners
- **Visualizer**: Scales with CSV size (~10MB per 10,000 rows)

### Network Impact
- **1 request per miner per 60 seconds**
- **~1KB response per request**
- **Concurrent requests** reduce total time

### File Sizes
- **CSV**: ~1MB per miner per day
- **PNG files**: 500KB-2MB each (300 DPI)

### Scalability Limits
- **Tested**: Up to 20 miners simultaneously
- **Network**: Limited by local network bandwidth
- **CPU**: Minimal usage, I/O bound operations
