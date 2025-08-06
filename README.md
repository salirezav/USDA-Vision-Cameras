# USDA Vision Camera System

A comprehensive system for monitoring machines via MQTT and automatically recording video from GigE cameras when machines are active. Designed for Atlanta, Georgia operations with proper timezone synchronization.

## 🎯 Overview

This system integrates MQTT machine monitoring with automated video recording from GigE cameras. When a machine turns on (detected via MQTT), the system automatically starts recording from the associated camera. When the machine turns off, recording stops and the video is saved with an Atlanta timezone timestamp.

### Key Features

- **🔄 MQTT Integration**: Listens to multiple machine state topics
- **📹 Automatic Recording**: Starts/stops recording based on machine states  
- **📷 GigE Camera Support**: Uses camera SDK library (mvsdk) for camera control
- **⚡ Multi-threading**: Concurrent MQTT listening, camera monitoring, and recording
- **🌐 REST API**: FastAPI server for dashboard integration
- **📡 WebSocket Support**: Real-time status updates
- **💾 Storage Management**: Organized file storage with cleanup capabilities
- **📝 Comprehensive Logging**: Detailed logging with rotation and error tracking
- **⚙️ Configuration Management**: JSON-based configuration system
- **🕐 Timezone Sync**: Proper time synchronization for Atlanta, Georgia

## 📁 Project Structure

```
USDA-Vision-Cameras/
├── README.md                    # Main documentation (this file)
├── main.py                      # System entry point
├── config.json                  # System configuration
├── requirements.txt             # Python dependencies
├── pyproject.toml              # UV package configuration
├── start_system.sh             # Startup script
├── setup_timezone.sh           # Time sync setup
├── camera_preview.html         # Web camera preview interface
├── usda_vision_system/         # Main application
│   ├── core/                   # Core functionality
│   ├── mqtt/                   # MQTT integration
│   ├── camera/                 # Camera management
│   ├── storage/                # File management
│   ├── api/                    # REST API server
│   └── main.py                 # Application coordinator
├── camera_sdk/                 # GigE camera SDK library
├── tests/                      # Organized test files
│   ├── api/                    # API-related tests
│   ├── camera/                 # Camera functionality tests
│   ├── core/                   # Core system tests
│   ├── mqtt/                   # MQTT integration tests
│   ├── recording/              # Recording feature tests
│   ├── storage/                # Storage management tests
│   ├── integration/            # System integration tests
│   └── legacy_tests/          # Archived development files
├── docs/                       # Organized documentation
│   ├── api/                    # API documentation
│   ├── features/               # Feature-specific guides
│   ├── guides/                 # User and setup guides
│   └── legacy/                 # Legacy documentation
├── ai_agent/                   # AI agent resources
│   ├── guides/                 # AI-specific instructions
│   ├── examples/               # Demo scripts and notebooks
│   └── references/             # API references and types
├── Camera/                     # Camera data directory
└── storage/                    # Recording storage (created at runtime)
    ├── camera1/               # Camera 1 recordings
    └── camera2/               # Camera 2 recordings
```

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
- GigE cameras compatible with camera SDK library
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
Ensure the `camera_sdk` directory contains the mvsdk library for your GigE cameras. This should include:
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

## 🌐 API Usage

The system provides a comprehensive REST API for monitoring and control.

> **📚 Complete API Documentation**: See [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for the full API reference including all endpoints, request/response models, examples, and recent enhancements.
>
> **⚡ Quick Reference**: See [docs/API_QUICK_REFERENCE.md](docs/API_QUICK_REFERENCE.md) for commonly used endpoints with curl examples.

### Starting the API Server
The API server starts automatically with the main system on port 8000:
```bash
python main.py
# API available at: http://localhost:8000
```

### 🚀 New API Features

#### Enhanced Recording Control
- **Dynamic camera settings**: Set exposure, gain, FPS per recording
- **Automatic datetime prefixes**: All filenames get timestamp prefixes
- **Auto-recording management**: Enable/disable per camera via API

#### Advanced Camera Configuration
- **Real-time settings**: Update image quality without restart
- **Live streaming**: MJPEG streams for web integration
- **Recovery operations**: Reconnect, reset, reinitialize cameras

#### Comprehensive Monitoring
- **MQTT event history**: Track machine state changes
- **Storage statistics**: Monitor disk usage and file counts
- **WebSocket updates**: Real-time system notifications

### Core Endpoints

#### System Status
```bash
# Get overall system status
curl http://localhost:8000/system/status

# Response example:
{
  "system_started": true,
  "mqtt_connected": true,
  "machines": {
    "vibratory_conveyor": {"state": "on", "last_updated": "2025-07-25T21:30:00-04:00"}
  },
  "cameras": {
    "camera1": {"status": "available", "is_recording": true}
  },
  "active_recordings": 1,
  "uptime_seconds": 3600
}
```

#### Machine Status
```bash
# Get all machine states
curl http://localhost:8000/machines

# Response example:
{
  "vibratory_conveyor": {
    "name": "vibratory_conveyor",
    "state": "on",
    "last_updated": "2025-07-25T21:30:00-04:00",
    "mqtt_topic": "vision/vibratory_conveyor/state"
  }
}
```

#### Camera Status
```bash
# Get all camera statuses
curl http://localhost:8000/cameras

# Get specific camera status
curl http://localhost:8000/cameras/camera1

# Response example:
{
  "name": "camera1",
  "status": "available",
  "is_recording": false,
  "last_checked": "2025-07-25T21:30:00-04:00",
  "device_info": {
    "friendly_name": "Blower-Yield-Cam",
    "serial_number": "054012620023"
  }
}
```

#### Manual Recording Control
```bash
# Start recording manually
curl -X POST http://localhost:8000/cameras/camera1/start-recording \
  -H "Content-Type: application/json" \
  -d '{"camera_name": "camera1", "filename": "manual_test.avi"}'

# Stop recording manually
curl -X POST http://localhost:8000/cameras/camera1/stop-recording

# Response example:
{
  "success": true,
  "message": "Recording started for camera1",
  "filename": "camera1_manual_20250725_213000.avi"
}
```

#### Storage Management
```bash
# Get storage statistics
curl http://localhost:8000/storage/stats

# Get recording files list
curl -X POST http://localhost:8000/storage/files \
  -H "Content-Type: application/json" \
  -d '{"camera_name": "camera1", "limit": 10}'

# Cleanup old files
curl -X POST http://localhost:8000/storage/cleanup \
  -H "Content-Type: application/json" \
  -d '{"max_age_days": 30}'
```

### WebSocket Real-time Updates
```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const update = JSON.parse(event.data);
    console.log('Real-time update:', update);

    // Handle different event types
    if (update.event_type === 'machine_state_changed') {
        console.log(`Machine ${update.data.machine_name} is now ${update.data.state}`);
    } else if (update.event_type === 'recording_started') {
        console.log(`Recording started: ${update.data.filename}`);
    }
};
```

### Integration Examples

#### Python Integration
```python
import requests
import json

# System status check
response = requests.get('http://localhost:8000/system/status')
status = response.json()
print(f"System running: {status['system_started']}")

# Start recording
recording_data = {"camera_name": "camera1"}
response = requests.post(
    'http://localhost:8000/cameras/camera1/start-recording',
    headers={'Content-Type': 'application/json'},
    data=json.dumps(recording_data)
)
result = response.json()
print(f"Recording started: {result['success']}")
```

#### JavaScript/React Integration
```javascript
// React hook for system status
import { useState, useEffect } from 'react';

function useSystemStatus() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/system/status');
        const data = await response.json();
        setStatus(data);
      } catch (error) {
        console.error('Failed to fetch status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  return status;
}

// Usage in component
function Dashboard() {
  const systemStatus = useSystemStatus();

  return (
    <div>
      <h1>USDA Vision System</h1>
      {systemStatus && (
        <div>
          <p>Status: {systemStatus.system_started ? 'Running' : 'Stopped'}</p>
          <p>MQTT: {systemStatus.mqtt_connected ? 'Connected' : 'Disconnected'}</p>
          <p>Active Recordings: {systemStatus.active_recordings}</p>
        </div>
      )}
    </div>
  );
}
```

#### Supabase Integration
```javascript
// Store recording metadata in Supabase
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Function to sync recording data
async function syncRecordingData() {
  try {
    // Get recordings from vision system
    const response = await fetch('http://localhost:8000/storage/files', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ limit: 100 })
    });
    const { files } = await response.json();

    // Store in Supabase
    for (const file of files) {
      await supabase.from('recordings').upsert({
        filename: file.filename,
        camera_name: file.camera_name,
        start_time: file.start_time,
        duration_seconds: file.duration_seconds,
        file_size_bytes: file.file_size_bytes
      });
    }
  } catch (error) {
    console.error('Sync failed:', error);
  }
}
```

## 📁 File Organization

The system organizes recordings in a structured format:

```
storage/
├── camera1/
│   ├── camera1_recording_20250725_213000.avi
│   ├── camera1_recording_20250725_214500.avi
│   └── camera1_manual_20250725_220000.avi
├── camera2/
│   ├── camera2_recording_20250725_213005.avi
│   └── camera2_recording_20250725_214505.avi
└── file_index.json
```

### Filename Convention
- **Format**: `{camera_name}_{type}_{YYYYMMDD_HHMMSS}.avi`
- **Timezone**: Atlanta local time (EST/EDT)
- **Examples**:
  - `camera1_recording_20250725_213000.avi` - Automatic recording
  - `camera1_manual_20250725_220000.avi` - Manual recording

## 🔍 Monitoring and Logging

### Log Files
- **Main Log**: `usda_vision_system.log` (rotated automatically)
- **Console Output**: Colored, real-time status updates
- **Component Logs**: Separate log levels for different components

### Log Levels
```bash
# Debug mode (verbose)
python main.py --log-level DEBUG

# Info mode (default)
python main.py --log-level INFO

# Warning mode (errors and warnings only)
python main.py --log-level WARNING
```

### Performance Monitoring
The system tracks:
- Startup times
- Recording session metrics
- MQTT message processing rates
- Camera status check intervals
- API response times

### Health Checks
```bash
# API health check
curl http://localhost:8000/health

# System status
curl http://localhost:8000/system/status

# Time synchronization
python check_time.py
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Camera Not Found
**Problem**: `Camera discovery failed` or `No cameras found`

**Solutions**:
```bash
# Check camera connections
ping 192.168.1.165  # Replace with your camera IP

# Verify camera SDK library
ls -la "camera_sdk/"
# Should contain mvsdk.py and related files

# Test camera discovery manually
python -c "
import sys; sys.path.append('./camera_sdk')
import mvsdk
devices = mvsdk.CameraEnumerateDevice()
print(f'Found {len(devices)} cameras')
for i, dev in enumerate(devices):
    print(f'Camera {i}: {dev.GetFriendlyName()}')
"

# Check camera permissions
sudo chmod 666 /dev/video*  # If using USB cameras
```

#### 2. MQTT Connection Failed
**Problem**: `MQTT connection failed` or `MQTT disconnected`

**Solutions**:
```bash
# Test MQTT broker connectivity
ping 192.168.1.110  # Replace with your broker IP
telnet 192.168.1.110 1883  # Test port connectivity

# Test MQTT manually
mosquitto_sub -h 192.168.1.110 -t "vision/+/state" -v

# Check credentials in config.json
{
  "mqtt": {
    "broker_host": "192.168.1.110",
    "broker_port": 1883,
    "username": "your_username",  # Add if required
    "password": "your_password"   # Add if required
  }
}

# Check firewall
sudo ufw status
sudo ufw allow 1883  # Allow MQTT port
```

#### 3. Recording Fails
**Problem**: `Failed to start recording` or `Camera initialization failed`

**Solutions**:
```bash
# Check storage permissions
ls -la storage/
chmod 755 storage/
chmod 755 storage/camera*/

# Check available disk space
df -h storage/

# Test camera initialization
python -c "
import sys; sys.path.append('./camera_sdk')
import mvsdk
devices = mvsdk.CameraEnumerateDevice()
if devices:
    try:
        hCamera = mvsdk.CameraInit(devices[0], -1, -1)
        print('Camera initialized successfully')
        mvsdk.CameraUnInit(hCamera)
    except Exception as e:
        print(f'Camera init failed: {e}')
"

# Check if camera is busy
lsof | grep video  # Check what's using cameras
```

#### 4. API Server Won't Start
**Problem**: `Failed to start API server` or `Port already in use`

**Solutions**:
```bash
# Check if port 8000 is in use
netstat -tlnp | grep 8000
lsof -i :8000

# Kill process using port 8000
sudo kill -9 $(lsof -t -i:8000)

# Use different port in config.json
{
  "system": {
    "api_port": 8001  # Change port
  }
}

# Check firewall
sudo ufw allow 8000
```

#### 5. Time Synchronization Issues
**Problem**: `Time is NOT synchronized` or time drift warnings

**Solutions**:
```bash
# Check time sync status
timedatectl status

# Force time sync
sudo systemctl restart systemd-timesyncd
sudo timedatectl set-ntp true

# Manual time sync
sudo ntpdate -s time.nist.gov

# Check timezone
timedatectl list-timezones | grep New_York
sudo timedatectl set-timezone America/New_York

# Verify with system
python check_time.py
```

#### 6. Storage Issues
**Problem**: `Permission denied` or `No space left on device`

**Solutions**:
```bash
# Check disk space
df -h
du -sh storage/

# Fix permissions
sudo chown -R $USER:$USER storage/
chmod -R 755 storage/

# Clean up old files
python -c "
from usda_vision_system.storage.manager import StorageManager
from usda_vision_system.core.config import Config
from usda_vision_system.core.state_manager import StateManager
config = Config()
state_manager = StateManager()
storage = StorageManager(config, state_manager)
result = storage.cleanup_old_files(7)  # Clean files older than 7 days
print(f'Cleaned {result[\"files_removed\"]} files')
"
```

### Debug Mode

Enable debug mode for detailed troubleshooting:
```bash
# Start with debug logging
python main.py --log-level DEBUG

# Check specific component logs
tail -f usda_vision_system.log | grep "camera"
tail -f usda_vision_system.log | grep "mqtt"
tail -f usda_vision_system.log | grep "ERROR"
```

### System Health Check

Run comprehensive system diagnostics:
```bash
# Full system test
python test_system.py

# Individual component tests
python test_timezone.py
python check_time.py

# API health check
curl http://localhost:8000/health
curl http://localhost:8000/system/status
```

### Log Analysis

Common log patterns to look for:
```bash
# MQTT connection issues
grep "MQTT" usda_vision_system.log | grep -E "(ERROR|WARNING)"

# Camera problems
grep "camera" usda_vision_system.log | grep -E "(ERROR|failed)"

# Recording issues
grep "recording" usda_vision_system.log | grep -E "(ERROR|failed)"

# Time sync problems
grep -E "(time|sync)" usda_vision_system.log | grep -E "(ERROR|WARNING)"
```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs**: Always start with `usda_vision_system.log`
2. **Run Tests**: Use `python test_system.py` to identify problems
3. **Check Configuration**: Verify `config.json` settings
4. **Test Components**: Use individual test scripts
5. **Check Dependencies**: Ensure all required packages are installed

### Performance Optimization

For better performance:
```bash
# Reduce camera check interval (in config.json)
{
  "system": {
    "camera_check_interval_seconds": 5  # Increase from 2 to 5
  }
}

# Optimize recording settings
{
  "cameras": [
    {
      "target_fps": 2.0,  # Reduce FPS for smaller files
      "exposure_ms": 2.0  # Adjust exposure as needed
    }
  ]
}

# Enable log rotation
{
  "system": {
    "log_level": "INFO"  # Reduce from DEBUG to INFO
  }
}
```

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone https://github.com/your-username/USDA-Vision-Cameras.git
cd USDA-Vision-Cameras

# Install development dependencies
uv sync --dev

# Run tests
python test_system.py
python test_timezone.py
```

### Project Structure
```
usda_vision_system/
├── core/           # Core functionality (config, state, events, logging)
├── mqtt/           # MQTT client and message handlers
├── camera/         # Camera management, monitoring, recording
├── storage/        # File management and organization
├── api/            # FastAPI server and WebSocket support
└── main.py         # Application coordinator
```

### Adding Features
1. **New Camera Types**: Extend `camera/recorder.py`
2. **New MQTT Topics**: Update `config.json` and `mqtt/handlers.py`
3. **New API Endpoints**: Add to `api/server.py`
4. **New Events**: Define in `core/events.py`

## 📄 License

This project is developed for USDA research purposes.

## 🆘 Support

For technical support:
1. Check the troubleshooting section above
2. Review logs in `usda_vision_system.log`
3. Run system diagnostics with `python test_system.py`
4. Check API health at `http://localhost:8000/health`

---

**System Status**: ✅ **READY FOR PRODUCTION**
**Time Sync**: ✅ **ATLANTA, GEORGIA (EDT/EST)**
**API Server**: ✅ **http://localhost:8000**
**Documentation**: ✅ **COMPLETE**
