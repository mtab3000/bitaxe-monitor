#!/bin/bash

# Bitaxe Monitor Docker Quick Start Script
# This script helps you quickly deploy the Bitaxe Monitor with Docker

set -e

echo "🔥 Bitaxe Monitor - Docker Deployment"
echo "======================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create data directory
mkdir -p data
mkdir -p config

echo "📂 Created data and config directories"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found!"
    echo "   Please ensure you're in the bitaxe-monitor directory"
    exit 1
fi

# Function to prompt for miner configuration
configure_miners() {
    echo ""
    echo "🔧 Miner Configuration"
    echo "====================="
    
    read -p "Enter miner names (comma-separated, e.g., Gamma-1,Gamma-2): " MINER_NAMES
    read -p "Enter miner IP addresses (comma-separated, e.g., 192.168.1.45,192.168.1.46): " MINER_IPS
    read -p "Enter miner ports (comma-separated, default 80,80): " MINER_PORTS
    
    # Set default ports if empty
    if [ -z "$MINER_PORTS" ]; then
        # Count commas in MINER_IPS to determine number of miners
        MINER_COUNT=$(echo "$MINER_IPS" | tr -cd ',' | wc -c)
        MINER_COUNT=$((MINER_COUNT + 1))
        MINER_PORTS=$(printf "80,%.0s" $(seq 1 $MINER_COUNT) | sed 's/,$//')
    fi
    
    echo ""
    echo "📋 Configuration Summary:"
    echo "   Names: $MINER_NAMES"
    echo "   IPs:   $MINER_IPS"
    echo "   Ports: $MINER_PORTS"
    echo ""
}

# Function to update docker-compose.yml
update_compose_file() {
    # Create a temporary file with updated environment variables
    sed -e "s/MINER_NAMES=.*/MINER_NAMES=$MINER_NAMES/" \
        -e "s/MINER_IPS=.*/MINER_IPS=$MINER_IPS/" \
        -e "s/MINER_PORTS=.*/MINER_PORTS=$MINER_PORTS/" \
        docker-compose.yml > docker-compose.yml.tmp
    
    mv docker-compose.yml.tmp docker-compose.yml
    echo "✅ Updated docker-compose.yml with your configuration"
}

# Main menu
echo ""
echo "Choose an option:"
echo "1) Configure miners and start monitoring"
echo "2) Start monitoring with existing configuration"
echo "3) Stop monitoring"
echo "4) View logs"
echo "5) Update and restart"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        configure_miners
        update_compose_file
        echo "🚀 Starting Bitaxe Monitor..."
        docker-compose up -d
        ;;
    2)
        echo "🚀 Starting Bitaxe Monitor with existing configuration..."
        docker-compose up -d
        ;;
    3)
        echo "🛑 Stopping Bitaxe Monitor..."
        docker-compose down
        echo "✅ Monitor stopped"
        exit 0
        ;;
    4)
        echo "📋 Showing logs (Press Ctrl+C to exit)..."
        docker-compose logs -f
        exit 0
        ;;
    5)
        echo "📦 Pulling latest updates..."
        docker-compose pull
        echo "🔄 Restarting monitor..."
        docker-compose up -d
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Wait a moment for container to start
sleep 5

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Bitaxe Monitor is running!"
    echo ""
    echo "🌐 Access the web interface:"
    echo "   - Local:    http://localhost:8080"
    echo "   - Network:  http://$(hostname -I | awk '{print $1}'):8080"
    echo ""
    echo "📊 Features available:"
    echo "   - Real-time charts (Hashrate, Efficiency, Variance, Voltage)"
    echo "   - Desktop and Mobile views"
    echo "   - Efficiency alerts"
    echo "   - Persistent data logging"
    echo ""
    echo "🔧 Useful commands:"
    echo "   docker-compose logs -f    # View logs"
    echo "   docker-compose down       # Stop monitor"
    echo "   docker-compose restart    # Restart monitor"
    echo ""
    echo "📁 Data is saved to: ./data/bitaxe_monitor_data.csv"
else
    echo ""
    echo "❌ Failed to start Bitaxe Monitor"
    echo "📋 Check logs for errors:"
    echo "   docker-compose logs"
    echo ""
    echo "🔧 Common issues:"
    echo "   - Check miner IP addresses are correct"
    echo "   - Ensure miners are powered on and accessible"
    echo "   - Verify no port conflicts on 8080"
fi
