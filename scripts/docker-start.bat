@echo off
:: Bitaxe Monitor Docker Quick Start Script for Windows
:: This script helps you quickly deploy the Bitaxe Monitor with Docker

echo 🔥 Bitaxe Monitor - Docker Deployment
echo ======================================

:: Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo    Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

:: Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Desktop first.
    echo    Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

:: Create data directory
if not exist "data" mkdir data
if not exist "config" mkdir config
echo 📂 Created data and config directories

:: Check if docker-compose.yml exists
if not exist "docker-compose.yml" (
    echo ❌ docker-compose.yml not found!
    echo    Please ensure you're in the bitaxe-monitor directory
    pause
    exit /b 1
)

echo.
echo Choose an option:
echo 1) Configure miners and start monitoring
echo 2) Start monitoring with existing configuration
echo 3) Stop monitoring
echo 4) View logs
echo 5) Update and restart
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto configure
if "%choice%"=="2" goto start_existing
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto update
echo ❌ Invalid choice
pause
exit /b 1

:configure
echo.
echo 🔧 Miner Configuration
echo =====================
set /p MINER_NAMES="Enter miner names (comma-separated, e.g., Gamma-1,Gamma-2): "
set /p MINER_IPS="Enter miner IP addresses (comma-separated, e.g., 192.168.1.45,192.168.1.46): "
set /p MINER_PORTS="Enter miner ports (comma-separated, default 80,80): "

:: Set default ports if empty
if "%MINER_PORTS%"=="" set MINER_PORTS=80,80,80

echo.
echo 📋 Configuration Summary:
echo    Names: %MINER_NAMES%
echo    IPs:   %MINER_IPS%
echo    Ports: %MINER_PORTS%
echo.

:: Note: Advanced sed replacement would require additional tools on Windows
:: For now, users can manually edit docker-compose.yml
echo ⚠️  Please manually update docker-compose.yml with these values
echo    MINER_NAMES=%MINER_NAMES%
echo    MINER_IPS=%MINER_IPS%
echo    MINER_PORTS=%MINER_PORTS%
echo.
pause

:start_existing
echo 🚀 Starting Bitaxe Monitor...
docker-compose up -d
goto check_status

:stop
echo 🛑 Stopping Bitaxe Monitor...
docker-compose down
echo ✅ Monitor stopped
pause
exit /b 0

:logs
echo 📋 Showing logs (Press Ctrl+C to exit)...
docker-compose logs -f
pause
exit /b 0

:update
echo 📦 Pulling latest updates...
docker-compose pull
echo 🔄 Restarting monitor...
docker-compose up -d
goto check_status

:check_status
:: Wait a moment for container to start
timeout /t 5 /nobreak >nul

:: Check if container is running
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo.
    echo ❌ Failed to start Bitaxe Monitor
    echo 📋 Check logs for errors:
    echo    docker-compose logs
    echo.
    echo 🔧 Common issues:
    echo    - Check miner IP addresses are correct
    echo    - Ensure miners are powered on and accessible
    echo    - Verify no port conflicts on 8080
) else (
    echo.
    echo ✅ Bitaxe Monitor is running!
    echo.
    echo 🌐 Access the web interface:
    echo    - Local:    http://localhost:8080
    echo    - Network:  http://YOUR_IP:8080
    echo.
    echo 📊 Features available:
    echo    - Real-time charts (Hashrate, Efficiency, Variance, Voltage^)
    echo    - Desktop and Mobile views
    echo    - Efficiency alerts
    echo    - Persistent data logging
    echo.
    echo 🔧 Useful commands:
    echo    docker-compose logs -f    # View logs
    echo    docker-compose down       # Stop monitor
    echo    docker-compose restart    # Restart monitor
    echo.
    echo 📁 Data is saved to: ./data/bitaxe_monitor_data.csv
)

pause
