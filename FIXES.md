# BitAxe Monitor - Fix Summary

## Issues Fixed (2025-06-24)

### 1. **Voltage Display Issues**
- **Fixed**: Set voltage showing 0 in overview
- **Solution**: Updated voltage field mapping to check multiple possible API field names:
  - `coreVoltageActual`, `asicVoltage`, `voltage` for measured voltage
  - `coreVoltage`, `targetVoltage`, `setVoltage` for set voltage
- **Added**: Automatic unit conversion (V to mV) with intelligent detection
- **Default**: Falls back to 1050mV if no set voltage found

### 2. **Voltage Display Format**
- **Changed**: Display voltage in millivolts (mV) instead of volts (V)
- **Updated**: Both web interface and console output now show "1050 mV" format
- **Renamed**: "Measured Voltage" label to "ASIC Voltage" for clarity

### 3. **Chart Improvements**
- **Fixed**: X-axis time labels going out of bounds
- **Added**: `maxTicksLimit: 8` to limit number of x-axis labels
- **Added**: Auto-rotation and auto-skip for x-axis labels to prevent overlap
- **Renamed**: Chart title from "Voltage & Temperature" to "ASIC Voltage"

### 4. **Documentation Updates**
- **Added**: Python virtual environment setup instructions
- **Added**: Step-by-step venv activation for Windows/macOS/Linux
- **Added**: Deactivation instructions
- **Updated**: Step numbering in Quick Start guide

### 5. **Debug Features**
- **Added**: Debug logging for first API response to help diagnose field names
- **Created**: `test_api.py` script to check BitAxe API response fields

## Testing the Fixes

1. **Run the test script first** to check API fields:
   ```bash
   python test_api.py
   ```

2. **Activate virtual environment**:
   ```bash
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Run the monitor** to see the fixes:
   ```bash
   python enhanced_bitaxe_monitor.py
   ```

## Notes
- The voltage field names may vary between BitAxe firmware versions
- The debug output will show the actual API fields on first run
- Default voltage is set to 1050mV if API doesn't provide the value
