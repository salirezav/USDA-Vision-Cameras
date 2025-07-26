# USDA Vision Camera System

A comprehensive system for monitoring machines via MQTT and automatically recording video from GigE cameras when machines are active. Designed for Atlanta, Georgia operations with proper timezone synchronization.

## 🎯 Overview

This system integrates MQTT machine monitoring with automated video recording from GigE cameras. When a machine turns on (detected via MQTT), the system automatically starts recording from the associated camera. When the machine turns off, recording stops and the video is saved with an Atlanta timezone timestamp.

### Key Features

- **🔄 MQTT Integration**: Listens to multiple machine state topics
- **📹 Automatic Recording**: Starts/stops recording based on machine states  
- **📷 GigE Camera Support**: Uses python demo library (mvsdk) for camera control
- **⚡ Multi-threading**: Concurrent MQTT listening, camera monitoring, and recording
- **🌐 REST API**: FastAPI server for dashboard integration
- **📡 WebSocket Support**: Real-time status updates
- **💾 Storage Management**: Organized file storage with cleanup capabilities
- **📝 Comprehensive Logging**: Detailed logging with rotation and error tracking
- **⚙️ Configuration Management**: JSON-based configuration system
- **🕐 Timezone Sync**: Proper time synchronization for Atlanta, Georgia

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MQTT Broker   │    │   GigE Camera   │    │   Dashboard     │
│                 │    │                 │    │   (React)       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ Machine States       │ Video Streams        │ API Calls
          │                      │                      │
┌─────────▼──────────────────────▼──────────────────────▼───────┐
│                USDA Vision Camera System                      │
├───────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ MQTT Client │  │   Camera    │  │ API Server  │           │
│  │             │  │  Manager    │  │             │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   State     │  │   Storage   │  │   Event     │           │
│  │  Manager    │  │  Manager    │  │  System     │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└───────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

### Hardware Requirements
- GigE cameras compatible with python demo library
- Network connection to MQTT broker
- Sufficient storage space for video recordings

### Software Requirements
- **Python 3.11+**
- **uv package manager** (recommended) or pip
- **MQTT broker** (e.g., Mosquitto, Home Assistant)
- **Linux system** (tested on Ubuntu/Debian)

### Network Requirements
- Access to MQTT broker
- GigE cameras on network
- Internet access for time synchronization (optional but recommended)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/USDA-Vision-Cameras.git
cd USDA-Vision-Cameras
```

### 2. Install Dependencies
Using uv (recommended):
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

Using pip:
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup GigE Camera Library
Ensure the `python demo` directory contains the mvsdk library for your GigE cameras. This should include:
- `mvsdk.py` - Python SDK wrapper
- Camera driver libraries
- Any camera-specific configuration files

### 4. Configure Storage Directory
```bash
# Create storage directory (adjust path as needed)
mkdir -p ./storage
# Or for system-wide storage:
# sudo mkdir -p /storage && sudo chown $USER:$USER /storage
```

### 5. Setup Time Synchronization (Recommended)
```bash
# Run timezone setup for Atlanta, Georgia
./setup_timezone.sh
```

### 6. Configure the System
Edit `config.json` to match your setup:
```json
{
  "mqtt": {
    "broker_host": "192.168.1.110",
    "broker_port": 1883,
    "topics": {
      "machine1": "vision/machine1/state",
      "machine2": "vision/machine2/state"
    }
  },
  "cameras": [
    {
      "name": "camera1",
      "machine_topic": "machine1",
      "storage_path": "./storage/camera1",
      "enabled": true
    }
  ]
}
```

## 🔧 Configuration

### MQTT Configuration
```json
{
  "mqtt": {
    "broker_host": "192.168.1.110",
    "broker_port": 1883,
    "username": null,
    "password": null,
    "topics": {
      "vibratory_conveyor": "vision/vibratory_conveyor/state",
      "blower_separator": "vision/blower_separator/state"
    }
  }
}
```

### Camera Configuration
```json
{
  "cameras": [
    {
      "name": "camera1",
      "machine_topic": "vibratory_conveyor",
      "storage_path": "./storage/camera1",
      "exposure_ms": 1.0,
      "gain": 3.5,
      "target_fps": 3.0,
      "enabled": true
    }
  ]
}
```

### System Configuration
```json
{
  "system": {
    "camera_check_interval_seconds": 2,
    "log_level": "INFO",
    "api_host": "0.0.0.0",
    "api_port": 8000,
    "enable_api": true,
    "timezone": "America/New_York"
  }
}
```

## 🎮 Usage

### Quick Start
```bash
# Test the system
python test_system.py

# Start the system
python main.py

# Or use the startup script
./start_system.sh
```

### Command Line Options
```bash
# Custom configuration file
python main.py --config my_config.json

# Debug mode
python main.py --log-level DEBUG

# Help
python main.py --help
```

### Verify Installation
```bash
# Run system tests
python test_system.py

# Check time synchronization
python check_time.py

# Test timezone functions
python test_timezone.py
```
