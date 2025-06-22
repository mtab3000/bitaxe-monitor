# Project Structure

This document describes the organization of the Bitaxe Monitor repository.

## Directory Structure

```
bitaxe-monitor/
├── src/                          # Main source code
│   ├── __init__.py              # Package initialization
│   ├── bitaxe_monitor.py        # Main enhanced monitor (primary script)
│   └── legacy/                  # Legacy versions (deprecated)
│       ├── bitaxe-monitor.py
│       ├── bitaxe-monitor-variance.py
│       ├── bitaxe_monitor_refactored.py
│       ├── bitaxe_monitor_refactored_nouni.py
│       └── raspi_monitor.py
├── docker/                      # Docker deployment files
│   ├── Dockerfile              # Container definition
│   ├── docker-compose.yml      # Multi-container orchestration
│   └── .dockerignore           # Docker build exclusions
├── scripts/                     # Helper scripts and utilities
│   ├── docker-start.sh         # Docker quick start (Linux/Mac)
│   ├── docker-start.bat        # Docker quick start (Windows)
│   ├── csv-visualizer.py       # Data visualization tool
│   ├── install.sh              # Installation script
│   ├── update.sh               # Update script
│   └── get-pip.py              # Pip installer
├── tests/                       # Unit tests and test utilities
│   ├── __init__.py             # Test package initialization
│   ├── test_bitaxe_monitor.py  # Main test suite
│   └── run_tests.py            # Test runner script
├── docs/                        # Documentation
│   ├── docker-deployment.md    # Docker deployment guide
│   ├── api_reference.md        # API documentation
│   └── troubleshooting.md      # Troubleshooting guide
├── examples/                    # Example configurations and scripts
├── config/                      # Configuration files and templates
│   └── config_example.json     # Example configuration
├── data/                        # Data files (CSV logs)
│   └── bitaxe_monitor_data.csv  # Main data file
├── .github/                     # GitHub workflows and templates
│   └── workflows/
│       └── quality.yml         # Code quality CI/CD pipeline
├── generated_charts/            # Generated visualization charts
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── README.md                   # Main project documentation
├── changelog.md                # Version history
├── license.txt                 # MIT license
├── SECURITY.md                 # Security policy
└── setup_guide.md             # Setup instructions
```

## File Purposes

### Core Application Files

- **`src/bitaxe_monitor.py`** - The main enhanced monitoring application with all features:
  - Web dashboard with mobile/desktop views
  - Real-time charts (hashrate, efficiency, variance, voltage)
  - Docker environment variable support
  - Persistent data logging
  - Raspberry Pi compatibility (ASCII console output)

- **`src/legacy/`** - Previous versions of the monitor for compatibility:
  - `bitaxe-monitor.py` - Original basic monitor
  - `bitaxe-monitor-variance.py` - Added variance tracking
  - `bitaxe_monitor_refactored.py` - Cleaned up version
  - `raspi_monitor.py` - Raspberry Pi specific version

### Docker Deployment

- **`docker/Dockerfile`** - Multi-stage container build with health checks
- **`docker/docker-compose.yml`** - Complete deployment configuration
- **`scripts/docker-start.sh/.bat`** - Interactive deployment scripts

### Development & Testing

- **`tests/`** - Comprehensive test suite with coverage reporting
- **`.github/workflows/quality.yml`** - Automated CI/CD pipeline with:
  - Pylint code analysis
  - Black code formatting checks
  - Bandit security scanning
  - Pytest unit testing
  - Docker build verification

### Configuration & Data

- **`config/`** - Configuration templates and examples
- **`data/`** - Persistent CSV data storage
- **`examples/`** - Usage examples and sample configurations

## Usage Patterns

### Development Workflow

1. **Local Development**: Use `src/bitaxe_monitor.py` directly
2. **Testing**: Run `python tests/run_tests.py` or use GitHub Actions
3. **Code Quality**: Automatic checks via GitHub workflows
4. **Docker Testing**: Use `docker-compose` in `docker/` directory

### Deployment Options

1. **Direct Python**: Run `python src/bitaxe_monitor.py`
2. **Docker**: Use `scripts/docker-start.sh` or manual `docker-compose`
3. **Production**: Use environment variables for configuration

### Legacy Support

- Legacy scripts in `src/legacy/` are maintained for compatibility
- New features only added to main `bitaxe_monitor.py`
- Migration path provided in documentation

## Key Features by Version

### Main Enhanced Version (`src/bitaxe_monitor.py`)
- ✅ Web dashboard with real-time charts
- ✅ Mobile/desktop responsive views  
- ✅ Variance tracking (60s, 300s, 600s windows)
- ✅ Docker deployment support
- ✅ Environment variable configuration
- ✅ Persistent data file (no new files on restart)
- ✅ Efficiency alerts with visual warnings
- ✅ Raspberry Pi ASCII compatibility
- ✅ All chart types visible simultaneously

### Legacy Versions (compatibility only)
- Basic monitoring and CSV logging
- Console-only output
- Hardcoded configuration
- Individual feature subsets

## Maintenance Notes

- **Primary development** focuses on `src/bitaxe_monitor.py`
- **Legacy versions** are frozen and only receive bug fixes
- **Docker images** automatically built from main version
- **Tests** cover main version functionality
- **Documentation** updated for main version features

This structure ensures clean separation of concerns while maintaining backward compatibility and supporting multiple deployment scenarios.
