# Bitaxe Performance Analysis Generator

## Overview

The Bitaxe Analysis Generator creates comprehensive HTML reports with 3D visualizations based on historic monitoring data. It analyzes the last 24 hours (configurable) of performance data to identify optimal settings for efficiency and low variance.

## Features

- **3D Surface Plots**: Interactive visualizations for hashrate, efficiency, and stability landscapes
- **Smart Recommendations**: Identifies optimal settings for different priorities (efficiency, stability, hashrate, balanced)
- **Quiet Operation Analysis**: Tracks fan speed to identify noise-friendly settings
- **Multi-Miner Comparison**: Compares performance across all miners
- **Historic Data Analysis**: Uses actual monitoring data to provide real-world recommendations

## Quick Start

### Prerequisites
```bash
# Install required dependencies
pip install pandas numpy
```

### Basic Usage
```bash
# Run analysis on last 24 hours of data
cd scripts
python bitaxe_analysis_generator.py

# Analyze different time windows
python bitaxe_analysis_generator.py --hours 12    # Last 12 hours
python bitaxe_analysis_generator.py --hours 48    # Last 48 hours
```

### Custom Paths
```bash
# Specify custom data and output directories
python bitaxe_analysis_generator.py \
    --data-dir /path/to/csv/files \
    --output-dir /path/to/output \
    --hours 24
```

## Output

The generator creates timestamped HTML files in the `generated_charts/` directory:
- `bitaxe_analysis_YYYYMMDD_HHMMSS.html`

### Report Sections

1. **Overall Champions** - Best performers across all miners
2. **Individual Miner Analysis** - Detailed breakdowns per miner
3. **3D Visualizations** - Interactive plots for each metric
4. **Final Recommendations** - Actionable optimization suggestions

### Visualization Types

- **Hashrate Landscape**: Shows performance across voltage/frequency combinations
- **Efficiency Landscape**: Identifies power-efficient operating points
- **Stability Landscape**: Maps variance across different settings
- **Correlation Analysis**: 3D scatter plot of efficiency vs stability vs voltage

## Data Requirements

### Input Data Format
The analyzer expects CSV files with these columns:
- `timestamp`: ISO format timestamps
- `miner_name`: Unique miner identifier (e.g., "Gamma-1")
- `set_voltage_v`: Set voltage in volts
- `frequency_mhz`: Frequency in MHz
- `hashrate_th`: Hashrate in TH/s
- `efficiency_j_th`: Efficiency in J/TH
- `actual_voltage_v`: Actual measured voltage
- `power_w`: Power consumption in watts
- `asic_temp_c`: ASIC temperature in Celsius
- `fan_speed_rpm`: Fan speed in RPM
- `fan_speed_percent`: Fan speed as percentage

### Minimum Data Requirements
- At least 5 measurements per voltage/frequency combination
- Data from the specified time window (default: 24 hours)
- Multiple voltage/frequency combinations for meaningful analysis

## Understanding the Results

### Recommendation Types

1. **Best Efficiency**: Lowest J/TH ratio (best power efficiency)
2. **Best Stability**: Lowest hashrate variance (most consistent)
3. **Best Hashrate**: Highest absolute performance
4. **Best Balanced**: Optimal combination of efficiency and stability

### Quiet Operation Analysis
- **Quiet**: Fan speed ≤ 60%
- **Loud**: Fan speed > 60%
- The analyzer identifies how many settings provide quiet operation

### Champions
- **Overall champions** compare across all miners
- **Individual analysis** shows best settings per miner
- Color-coded cards highlight different optimization priorities

## Integration with Monitoring

### Automatic Analysis
You can set up automated analysis generation:

```bash
# Add to crontab for hourly analysis
0 * * * * cd /path/to/bitaxe-monitor/scripts && python bitaxe_analysis_generator.py --hours 24
```

### Docker Integration
If using Docker deployment, mount the analysis script:

```yaml
volumes:
  - ./scripts:/app/scripts
  - ./generated_charts:/app/generated_charts
```

Then run analysis inside container:
```bash
docker exec bitaxe-monitor python /app/scripts/bitaxe_analysis_generator.py
```

## Troubleshooting

### Common Issues

**No CSV files found**
- Ensure the monitor has been running and generating data
- Check the `--data-dir` path is correct
- Verify CSV files exist in the data directory

**Insufficient data for analysis**
- Ensure at least 5 measurements per setting combination
- Try increasing the `--hours` parameter
- Check that miners have been tested at different voltage/frequency settings

**Empty visualizations**
- Verify data contains the required columns
- Check that there are multiple voltage/frequency combinations
- Ensure timestamps are within the specified time window

**Missing dependencies**
```bash
pip install pandas numpy plotly
```

## Advanced Usage

### Custom Time Windows
```bash
# Last 6 hours for recent optimization results
python bitaxe_analysis_generator.py --hours 6

# Last week for comprehensive analysis
python bitaxe_analysis_generator.py --hours 168
```

### Batch Processing
```bash
# Generate multiple reports
for hours in 6 12 24 48; do
    python bitaxe_analysis_generator.py --hours $hours
done
```

## Output Interpretation

### 3D Surface Plots
- **X-axis**: Set voltage (mV)
- **Y-axis**: Frequency (MHz)  
- **Z-axis**: Performance metric (hashrate, efficiency, stability)
- **Color**: Intensity of the metric value

### Correlation Plots
- Show relationships between efficiency, stability, and actual voltage
- Hover for detailed setting information
- Identify sweet spots where multiple metrics are optimal

### Recommendations
- **Green highlights**: Optimal settings
- **Yellow borders**: Balanced recommendations
- **Red warnings**: Loud operation alerts
- **Blue accents**: Quiet operation options

The analysis generator provides actionable insights to optimize your Bitaxe miners based on real performance data rather than theoretical calculations.
