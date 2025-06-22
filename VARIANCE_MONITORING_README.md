# Enhanced Variance Monitoring Features

## Overview

The Enhanced Variance Monitoring system provides comprehensive tracking and analysis of hashrate variance patterns across different time windows. This system distinguishes between positive and negative deviations from expected hashrate baselines, enabling detailed performance analysis and stability assessment.

## Key Features Implemented

### ✅ Directional Variance Tracking
- **Positive Variance**: Tracks performance above expected hashrate
- **Negative Variance**: Tracks performance below expected hashrate  
- **Average Deviation**: Real-time deviation from expected baseline
- **Separate tracking** for each variance type with individual statistics

### ✅ Multi-Window Analysis
- **60-second window**: Short-term variance for immediate issues
- **300-second window**: Medium-term trends and stability
- **600-second window**: Long-term performance patterns
- **Real-time calculation** and display for all windows

### ✅ Expected Hashrate Baseline
- **Automatic calculation** based on ASIC model and frequency
- **Manual override support** for custom expected rates
- **Dynamic baseline** updates with frequency changes
- **Model-specific calculations** for BM1370, BM1368, BM1366, BM1397

### ✅ Enhanced Data Persistence
- **CSV Logging**: `variance_tracking.csv` with detailed variance metrics
- **SQLite Database**: `variance_analytics.db` for analytics and reporting
- **Daily Summaries**: Automated daily variance summaries
- **Historical Storage**: Long-term variance trend storage

### ✅ Stability Scoring System
- **0-100 Scale**: Higher scores indicate more stable performance
- **Multi-factor calculation**: Based on deviation and variance levels
- **Real-time scoring**: Updated with each measurement cycle
- **Historical tracking**: Trend analysis over time

### ✅ Web Dashboard Integration
- **Enhanced Analytics View**: Dedicated variance monitoring section
- **Real-time Charts**: Directional variance visualization
- **Interactive Reports**: Generate detailed variance reports
- **Mobile/Desktop Support**: Responsive design for all devices

## New Data Fields

### CSV Fields Added
```
hashrate_positive_variance_60s    - Positive variance (60s window)
hashrate_positive_variance_300s   - Positive variance (300s window) 
hashrate_positive_variance_600s   - Positive variance (600s window)
hashrate_negative_variance_60s    - Negative variance (60s window)
hashrate_negative_variance_300s   - Negative variance (300s window)
hashrate_negative_variance_600s   - Negative variance (600s window)
hashrate_avg_deviation_60s        - Average deviation (60s window)
hashrate_avg_deviation_300s       - Average deviation (300s window)
hashrate_avg_deviation_600s       - Average deviation (600s window)
```

### Database Tables Added
```sql
variance_metrics              - Detailed variance measurements
variance_summary             - Daily variance summaries
```

## API Endpoints

### New Variance Endpoints
- `GET /api/variance/summary` - Current variance summary for all miners
- `GET /api/variance/analytics/<miner>?days=N` - Detailed analytics for specific miner
- `GET /api/variance/report/<miner>?days=N` - Generate detailed variance report

### Response Examples

#### Variance Summary
```json
{
  "timestamp": "2025-06-22T20:06:10",
  "miner_summaries": {
    "Gamma-1": {
      "stability_score": 85.2,
      "efficiency_pct": 99.7,
      "current_deviation": +5.3,
      "variance_60s": 12.4,
      "variance_300s": 18.7,
      "variance_600s": 23.1
    }
  }
}
```

#### Analytics Response
```json
{
  "miner_name": "Gamma-1",
  "analysis_period_days": 7,
  "variance_trends": [
    {
      "window_seconds": 60,
      "avg_pos_var": 15.2,
      "avg_neg_var": 12.8,
      "avg_stability": 82.4,
      "sample_count": 1440
    }
  ],
  "worst_stability_periods": [...],
  "best_stability_periods": [...]
}
```

## Web Interface Enhancements

### Enhanced Variance Analytics Dashboard
- **Toggle Button**: "Show Enhanced Variance Analytics"
- **Analytics Tab**: Real-time variance summary cards
- **Reports Tab**: Generate and view detailed reports
- **Interactive Charts**: Directional variance visualization

### Chart Types Added
- **Directional Variance Chart**: Shows positive/negative deviations relative to expected hashrate baseline
- **Stability Score Trends**: Historical stability scoring
- **Variance Distribution**: Statistical variance analysis

### Variance Cards Display
- **Color-coded status**: Green (stable), Yellow (medium), Red (high variance)
- **Stability Score**: 0-100 scoring with trend indicators
- **Real-time metrics**: Current deviation, efficiency, variance levels
- **Multi-window data**: All three time windows displayed

## Configuration

### Environment Variables
```bash
# Enable enhanced variance tracking (default: enabled)
ENABLE_VARIANCE_TRACKING=true

# Variance data directory (default: data/)
VARIANCE_DATA_DIR=data

# Daily summary generation (default: enabled)
GENERATE_DAILY_SUMMARIES=true
```

### Manual Expected Hashrates
```python
expected_hashrates = {
    'Gamma-1': 1200,  # Force 1200 GH/s expected
    'Gamma-2': 1150,  # Force 1150 GH/s expected
    'Gamma-3': 1100,  # Force 1100 GH/s expected
}
```

## File Structure

```
bitaxe-monitor/
├── src/
│   ├── bitaxe_monitor.py        # Main monitor (enhanced)
│   ├── variance_persistence.py  # Variance data storage
│   └── variance_dashboard.py    # Dashboard HTML components
├── data/
│   ├── bitaxe_monitor_data.csv    # Main metrics CSV
│   ├── variance_tracking.csv      # Variance-specific CSV
│   └── variance_analytics.db      # SQLite analytics database
└── test_variance_features.py      # Validation test script
```

## Usage Instructions

### 1. Basic Usage
```bash
# Start the enhanced monitor
python src/bitaxe_monitor.py

# Open web interface
http://localhost:8080

# Click "Show Enhanced Variance Analytics"
```

### 2. Advanced Configuration
```python
# Custom expected hashrates
monitor = MultiBitaxeMonitor(
    miners_config=miners_config,
    expected_hashrates={
        'Gamma-1': 1200,
        'Gamma-2': 1150,
        'Gamma-3': 1100
    }
)
```

### 3. API Integration
```python
import requests

# Get variance summary
response = requests.get('http://localhost:8080/api/variance/summary')
data = response.json()

# Get detailed analytics
response = requests.get('http://localhost:8080/api/variance/analytics/Gamma-1?days=7')
analytics = response.json()
```

### 4. Report Generation
```bash
# Via web interface: Reports tab -> Select miner -> Generate Report
# Via API: GET /api/variance/report/Gamma-1?days=30
```

## Variance Interpretation

### Stability Scores
- **90-100**: Excellent stability, minimal variance
- **80-89**: Good stability, acceptable variance
- **70-79**: Medium stability, monitor for issues
- **60-69**: Poor stability, investigate causes
- **0-59**: Critical instability, immediate attention required

### Variance Thresholds
- **Low Variance**: <20 GH/s standard deviation
- **Medium Variance**: 20-40 GH/s standard deviation
- **High Variance**: >40 GH/s standard deviation

### Deviation Analysis
- **Positive Deviation**: Performance above expected (good)
- **Negative Deviation**: Performance below expected (investigate)
- **Consistent Deviation**: May indicate need for expected hashrate adjustment

## Troubleshooting

### Common Issues

#### High Variance Warnings
```
CAUSE: Temperature fluctuations, power instability, network issues
SOLUTION: Check cooling, power supply, network stability
```

#### Low Stability Scores
```
CAUSE: Inconsistent performance, hardware issues
SOLUTION: Monitor temperatures, voltages, frequency settings
```

#### Missing Variance Data
```
CAUSE: Insufficient data points, recent startup
SOLUTION: Wait for data accumulation (minimum 2 samples per window)
```

### Debug Endpoints
- `GET /api/debug/<miner>` - Raw history data inspection
- `GET /api/variance/analytics/<miner>` - Detailed variance analytics

## Performance Considerations

### Data Storage
- **CSV files**: Continuous append, no rotation
- **SQLite database**: Optimized with indexes for fast queries
- **Memory usage**: Efficient deque-based history storage

### Update Frequency
- **Real-time calculations**: Every polling cycle (60s default)
- **Daily summaries**: Generated at midnight
- **Web updates**: Every 5 seconds

### Scalability
- **Multi-miner support**: Concurrent processing
- **Large datasets**: Efficient window-based calculations
- **Long-term storage**: Compressed historical data

## Testing

### Validation Script
```bash
# Run comprehensive feature validation
python test_variance_features.py

# Expected output: All tests passed
```

### Manual Testing
1. Start monitor with test miners
2. Verify variance data appears in web interface
3. Check CSV and database files are created
4. Generate variance reports
5. Validate API responses

## Future Enhancements

### Planned Features
- **Predictive Analytics**: Machine learning variance prediction
- **Alert System**: Email/webhook notifications for high variance
- **Comparative Analysis**: Fleet-wide variance comparison
- **Export Formats**: PDF reports, Excel exports
- **Historical Charts**: Long-term variance trend visualization

## Support

For issues or questions regarding the Enhanced Variance Monitoring system:

1. Check the troubleshooting section above
2. Run the validation script: `python test_variance_features.py`
3. Review log files for error messages
4. Verify data files are being created in the `data/` directory

## Version Information

- **Implementation Date**: June 22, 2025
- **Branch**: test-pylint-enhancements
- **Compatibility**: Python 3.7+, Flask 2.0+, SQLite 3.0+
