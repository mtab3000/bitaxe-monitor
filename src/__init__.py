"""
Bitaxe Monitor - Enhanced Multi-Miner Monitoring System

A comprehensive Python monitoring tool for multiple Bitaxe miners with real-time 
performance metrics, variance tracking, web interface, and Docker support.

Features:
- Multi-miner concurrent monitoring
- Real-time web dashboard with mobile/desktop views
- Hashrate variance tracking and efficiency analysis
- Docker deployment with environment-based configuration
- Persistent data logging to CSV
- Visual alerts for performance issues
- Raspberry Pi compatible (ASCII-only console output)

Author: mtab3000
License: MIT
"""

__version__ = "2.0.0"
__author__ = "mtab3000"
__license__ = "MIT"

# Import main classes for easier access
try:
    from .bitaxe_monitor import (
        MinerConfig,
        ASICSpecs,
        HashrateHistory,
        MinerMetrics,
        BitaxeAPI,
        MetricsCollector,
        DataLogger,
        Display,
        WebServer,
        MultiBitaxeMonitor,
        load_config_from_env,
        main
    )
except ImportError:
    # Handle import errors gracefully for testing
    pass

__all__ = [
    'MinerConfig',
    'ASICSpecs', 
    'HashrateHistory',
    'MinerMetrics',
    'BitaxeAPI',
    'MetricsCollector',
    'DataLogger',
    'Display',
    'WebServer',
    'MultiBitaxeMonitor',
    'load_config_from_env',
    'main'
]
