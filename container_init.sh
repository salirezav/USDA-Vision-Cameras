#!/bin/bash

# Container initialization script for USDA Vision Camera System
# This script sets up and starts the systemd service in a container environment

echo "🐳 Container Init - USDA Vision Camera System"
echo "============================================="

# Start systemd if not already running (for containers)
if ! pgrep systemd > /dev/null; then
    echo "🔧 Starting systemd..."
    exec /sbin/init &
    sleep 5
fi

# Setup the service if not already installed
if [ ! -f "/etc/systemd/system/usda-vision-camera.service" ]; then
    echo "📦 Setting up USDA Vision Camera service..."
    cd /home/alireza/USDA-vision-cameras
    sudo ./setup_service.sh
fi

# Start the service
echo "🚀 Starting USDA Vision Camera service..."
sudo systemctl start usda-vision-camera

# Follow the logs
echo "📋 Following service logs (Ctrl+C to exit)..."
sudo journalctl -u usda-vision-camera -f
