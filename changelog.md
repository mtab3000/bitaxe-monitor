# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-06-18

### Added
- **Expected hashrate calculation** based on ASIC model and frequency
- **Efficiency percentage** with visual indicators (🔥⚡⚠️)
- **Set voltage monitoring** alongside actual voltage
- **Comprehensive ASIC support** for BM1370, BM1368, BM1366, BM1397
- **Fleet-wide statistics** and averages
- **Enhanced CSV logging** with all new metrics
- **Clean table formatting** with proper alignment
- **Modular architecture** with separate classes for better maintainability

### Changed
- **Completely refactored** codebase for Python 3.6+ compatibility
- **Improved display format** with cleaner, more readable output
- **Enhanced error handling** and logging
- **30-second polling** with consistent timing
- **Concurrent data collection** for faster updates

### Fixed
- **Column alignment issues** in display output
- **Unicode compatibility** problems in various terminals
- **Memory efficiency** improvements
- **Network timeout handling**

### Technical Details
- Replaced dataclasses with regular classes for Python 3.6 compatibility
- Added ASICSpecs class for expected hashrate calculations
- Implemented proper CSV header management
- Enhanced metrics collection with voltage and efficiency tracking

## [1.0.0] - 2024-XX-XX

### Added
- Initial release
- Basic multi-miner monitoring
- CSV data logging
- Temperature and power monitoring
- Simple display output

### Features
- Monitor multiple Bitaxe miners
- Real-time hashrate and power consumption
- Basic temperature monitoring
- CSV export functionality