# Changelog

All notable changes to the Bitaxe Monitor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-06-22

### 🧠 Added Historic Data Analysis & AI-Powered Optimization

#### Added
- **Historic Data Analysis Generator**: `scripts/bitaxe_analysis_generator.py`
  - Analyzes last 24 hours (configurable) of monitoring data
  - Generates comprehensive HTML reports with interactive 3D visualizations
  - Smart recommendations for optimal voltage/frequency combinations
  - Identifies sweet spots for efficiency and low variance operation
  - Multi-miner performance comparison with champion identification
  - Quiet operation analysis (fan speed < 60%) with noise-friendly settings
  - Beautiful HTML reports with Plotly.js 3D surface plots and correlation analysis

#### Enhanced Features
- **3D Performance Landscapes**: Interactive visualizations showing hashrate, efficiency, and stability across voltage/frequency combinations
- **AI-Powered Recommendations**: Data-driven optimization suggestions based on actual performance patterns
- **Comprehensive Analysis Reports**: Professional HTML output with actionable insights
- **Real-World Optimization**: Uses actual monitoring data rather than theoretical calculations
- **Time Window Flexibility**: Configurable analysis periods (6, 12, 24, 48+ hours)

#### Dependencies
- Added pandas and numpy to requirements for data analysis capabilities
- Enhanced documentation with analysis generator usage guide

## [2.0.0] - 2025-06-22

### 🎉 Major Release - Complete Rewrite with Web Interface

#### Added
- **Enhanced Web Dashboard**: Full-featured web interface accessible at http://localhost:8080
- **Real-time Charts**: Hashrate, efficiency, variance, and voltage tracking over time
- **Mobile/Desktop Views**: Responsive design with toggle between optimized layouts
- **Persistent Charts**: Graphs never disappear or reset between updates
- **Docker Support**: Complete containerized deployment with docker-compose
- **Environment Configuration**: Configure miners via environment variables (Docker mode)
- **Variance Tracking**: Monitor hashrate stability over 60s, 300s, 600s windows
- **Visual Alerts**: Background turns red when efficiency drops below 80%
- **Multi-Chart View**: All chart types visible simultaneously (stacked layout)
- **Raspberry Pi Compatibility**: ASCII-only console output (no Unicode issues)
- **Persistent Data File**: Single CSV file that survives restarts
- **GitHub Workflows**: Automated CI/CD with pylint, testing, and Docker builds
- **Comprehensive Testing**: Unit tests with coverage reporting
- **Project Structure**: Organized repository with proper directory structure

#### Enhanced Console Output
- **Variance Columns**: Added s60s, s300s, s600s standard deviation tracking
- **Variance Rating**: STABLE/MEDIUM/HIGH! indicators for hashrate stability
- **ASCII Symbols**: Replaced Unicode with ASCII for Raspberry Pi compatibility
- **Enhanced Information**: More detailed voltage and frequency information

#### Docker Features
- **Interactive Setup Scripts**: `scripts/docker-start.sh` and `docker-start.bat`
- **Environment-based Config**: No more hardcoded IP addresses
- **Health Checks**: Built-in container monitoring
- **Persistent Volumes**: Data survives container updates
- **Auto-restart**: Container recovery on failure

#### Technical Improvements
- **Code Quality**: Pylint compliance and automated quality checks
- **Type Safety**: Better error handling and input validation
- **Performance**: Optimized chart updates and data handling
- **Architecture**: Clean separation of concerns with modular design
- **Documentation**: Comprehensive guides for deployment and development

### Changed
- **Main Script**: Renamed to `src/bitaxe_monitor.py` (enhanced version)
- **Polling Interval**: Changed default from 30s to 60s for better stability
- **Data Storage**: Single persistent file instead of timestamped files
- **Console Output**: Removed Unicode characters for Raspberry Pi compatibility
- **Project Structure**: Organized files into logical directories

### Deprecated
- **Legacy Scripts**: Moved older versions to `src/legacy/` directory
  - `bitaxe-monitor.py` (original)
  - `bitaxe-monitor-variance.py` (console variance)
  - `bitaxe_monitor_refactored.py` (cleaned version)
  - `raspi_monitor.py` (Pi-specific)

### Migration Guide
- **From v1.x to v2.0**: Use `src/bitaxe_monitor.py` instead of older scripts
- **Docker Users**: Update paths in docker-compose.yml to use new structure
- **Data Files**: Existing CSV files will continue to be appended to

## [1.2.0] - 2025-06-18

### Added
- Variance tracking for hashrate analysis
- Enhanced console output with variance indicators
- Better efficiency calculations and warnings

### Changed
- Improved error handling for network timeouts
- Better ASIC model detection

## [1.1.0] - 2025-06-15

### Added
- Expected hashrate calculation based on ASIC specs
- Efficiency percentage indicators
- Fleet-wide statistics and averages
- Enhanced CSV logging with more metrics

### Changed
- Concurrent data collection for better performance
- Improved console formatting and readability

## [1.0.0] - 2025-06-10

### Added
- Initial release of Multi-Bitaxe Monitor
- Basic monitoring for multiple miners
- CSV data logging
- Console output with miner statistics
- Support for BM1370, BM1368, BM1366, BM1397 ASICs

### Features
- Real-time hashrate monitoring
- Power consumption tracking
- Temperature monitoring
- Pool connection status
- Basic efficiency calculations

---

## Development Notes

### Version 2.0.0 Architecture Changes

The 2.0.0 release represents a complete architectural overhaul:

1. **Web-First Design**: Primary interface moved from console to web dashboard
2. **Docker Native**: Built from ground up for containerized deployment
3. **Mobile Support**: Responsive design for all device types
4. **Real-time Updates**: Live charts with persistent data
5. **Environment Config**: Container-friendly configuration system
6. **Quality Assurance**: Automated testing and code quality checks

### Breaking Changes in 2.0.0

- **File Locations**: Main script moved to `src/bitaxe_monitor.py`
- **Configuration**: Environment variables now preferred over hardcoded config
- **Data Files**: Single persistent file instead of timestamped files
- **Console Output**: ASCII-only (no Unicode) for better compatibility
- **Dependencies**: Added Flask for web interface

### Upgrade Path

1. **Docker Users** (Recommended):
   ```bash
   # Use new docker-compose.yml structure
   cd docker/
   docker-compose up -d
   ```

2. **Local Users**:
   ```bash
   # Use new main script
   python src/bitaxe_monitor.py
   ```

3. **Legacy Users**:
   ```bash
   # Continue using legacy scripts
   python src/legacy/bitaxe_monitor_refactored.py
   ```

### Future Roadmap

- **v2.1.0**: Advanced alerting and notification system
- **v2.2.0**: Historical data analysis and trending
- **v2.3.0**: Multiple pool monitoring and failover detection
- **v3.0.0**: Bitaxe firmware integration and remote configuration
