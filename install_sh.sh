#!/bin/bash

# Multi-Bitaxe Monitor Installation Script

echo "🔥 Multi-Bitaxe Monitor Installation"
echo "===================================="

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.6+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.6"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION+ is required."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Install dependencies
echo "📦 Installing dependencies..."
if pip3 install -r requirements.txt; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create config file if it doesn't exist
if [ ! -f "config.json" ]; then
    echo "📝 Creating configuration file..."
    cp config.example.json config.json
    echo "✅ Configuration file created: config.json"
    echo "💡 Please edit config.json with your miner IP addresses"
else
    echo "✅ Configuration file already exists"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your Bitaxe miner IP addresses"
echo "2. Run: python3 bitaxe_monitor_refactored.py"
echo ""
echo "For more information, see README.md"