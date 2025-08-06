#!/bin/bash

# USDA Vision Camera System Service Setup Script

echo "USDA Vision Camera System - Service Setup"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Get the current directory (where the script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/usda-vision-camera.service"

echo "📁 Working directory: $SCRIPT_DIR"

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Service file not found: $SERVICE_FILE"
    exit 1
fi

# Make start_system.sh executable
echo "🔧 Making start_system.sh executable..."
chmod +x "$SCRIPT_DIR/start_system.sh"

# Update the service file with the correct path
echo "📝 Updating service file with correct paths..."
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|g" "$SERVICE_FILE"
sed -i "s|ExecStart=.*|ExecStart=/bin/bash $SCRIPT_DIR/start_system.sh|g" "$SERVICE_FILE"

# Copy service file to systemd directory
echo "📋 Installing service file..."
cp "$SERVICE_FILE" /etc/systemd/system/

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable the service
echo "✅ Enabling USDA Vision Camera service..."
systemctl enable usda-vision-camera.service

# Check service status
echo "📊 Service status:"
systemctl status usda-vision-camera.service --no-pager

echo ""
echo "🎉 Service setup complete!"
echo ""
echo "Available commands:"
echo "  sudo systemctl start usda-vision-camera    # Start the service"
echo "  sudo systemctl stop usda-vision-camera     # Stop the service"
echo "  sudo systemctl restart usda-vision-camera  # Restart the service"
echo "  sudo systemctl status usda-vision-camera   # Check service status"
echo "  sudo journalctl -u usda-vision-camera -f   # View live logs"
echo ""
echo "The service will automatically start when the container/system boots."
