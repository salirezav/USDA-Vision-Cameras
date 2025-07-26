#!/bin/bash

# USDA Vision Camera System Startup Script

echo "USDA Vision Camera System - Startup Script"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run 'uv sync' first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if config file exists
if [ ! -f "config.json" ]; then
    echo "⚠️  Config file not found. Using default configuration."
fi

# Check storage directory
if [ ! -d "/storage" ]; then
    echo "📁 Creating storage directory..."
    sudo mkdir -p /storage
    sudo chown $USER:$USER /storage
    echo "✅ Storage directory created at /storage"
fi

# Check time synchronization
echo "🕐 Checking time synchronization..."
python check_time.py
echo ""
# Run system tests first
echo "🧪 Running system tests..."
python test_system.py

if [ $? -ne 0 ]; then
    echo "❌ System tests failed. Please check the configuration."
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 Starting USDA Vision Camera System..."
echo "   - MQTT monitoring will begin automatically"
echo "   - Camera recording will start when machines turn on"
echo "   - API server will be available at http://localhost:8000"
echo "   - Press Ctrl+C to stop the system"
echo ""

# Start the system
python main.py "$@"

echo "👋 USDA Vision Camera System stopped."
