# USDA Vision Camera System

A comprehensive system for monitoring machines via MQTT and automatically recording video from GigE cameras when machines are active.

## Overview

This system integrates MQTT machine monitoring with automated video recording from GigE cameras. When a machine turns on (detected via MQTT), the system automatically starts recording from the associated camera. When the machine turns off, recording stops and the video is saved with a timestamp.

## Features

- **MQTT Integration**: Listens to multiple machine state topics
- **Automatic Recording**: Starts/stops recording based on machine states
- **GigE Camera Support**: Uses the python demo library (mvsdk) for camera control
- **Multi-threading**: Concurrent MQTT listening, camera monitoring, and recording
- **REST API**: FastAPI server for dashboard integration
- **WebSocket Support**: Real-time status updates
- **Storage Management**: Organized file storage with cleanup capabilities
- **Comprehensive Logging**: Detailed logging with rotation and error tracking
- **Configuration Management**: JSON-based configuration system

## Architecture

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

## Installation

1. **Prerequisites**:
   - Python 3.11+
   - GigE cameras with python demo library
   - MQTT broker (e.g., Mosquitto)
   - uv package manager (recommended)

2. **Install Dependencies**:
   ```bash
   uv sync
   ```

3. **Setup Storage Directory**:
   ```bash
   sudo mkdir -p /storage
   sudo chown $USER:$USER /storage
   ```

## Configuration

Edit `config.json` to configure your system:

```json
{
  "mqtt": {
    "broker_host": "192.168.1.110",
    "broker_port": 1883,
    "topics": {
      "vibratory_conveyor": "vision/vibratory_conveyor/state",
      "blower_separator": "vision/blower_separator/state"
    }
  },
  "cameras": [
    {
      "name": "camera1",
      "machine_topic": "vibratory_conveyor",
      "storage_path": "/storage/camera1",
      "exposure_ms": 1.0,
      "gain": 3.5,
      "target_fps": 3.0,
      "enabled": true
    }
  ]
}
```

## Usage

### Basic Usage

1. **Start the System**:
   ```bash
   python main.py
   ```

2. **With Custom Config**:
   ```bash
   python main.py --config my_config.json
   ```

3. **Debug Mode**:
   ```bash
   python main.py --log-level DEBUG
   ```

### API Endpoints

The system provides a REST API on port 8000:

- `GET /system/status` - Overall system status
- `GET /cameras` - All camera statuses
- `GET /machines` - All machine states
- `POST /cameras/{name}/start-recording` - Manual recording start
- `POST /cameras/{name}/stop-recording` - Manual recording stop
- `GET /storage/stats` - Storage statistics
- `WebSocket /ws` - Real-time updates

### Dashboard Integration

The system is designed to integrate with your existing React + Vite + Tailwind + Supabase dashboard:

1. **API Integration**: Use the REST endpoints to display system status
2. **WebSocket**: Connect to `/ws` for real-time updates
3. **Supabase Storage**: Store recording metadata and system logs

## File Organization

```
/storage/
├── camera1/
│   ├── camera1_recording_20250726_143022.avi
│   └── camera1_recording_20250726_143155.avi
├── camera2/
│   ├── camera2_recording_20250726_143025.avi
│   └── camera2_recording_20250726_143158.avi
└── file_index.json
```

## Monitoring and Logging

### Log Files

- `usda_vision_system.log` - Main system log (rotated)
- Console output with colored formatting
- Component-specific log levels

### Performance Monitoring

The system includes built-in performance monitoring:
- Startup times
- Recording session metrics
- MQTT message processing rates
- Camera status check intervals

### Error Tracking

Comprehensive error tracking with:
- Error counts per component
- Detailed error context
- Automatic recovery attempts

## Troubleshooting

### Common Issues

1. **Camera Not Found**:
   - Check camera connections
   - Verify python demo library installation
   - Run camera discovery: Check logs for enumeration results

2. **MQTT Connection Failed**:
   - Verify broker IP and port
   - Check network connectivity
   - Verify credentials if authentication is enabled

3. **Recording Fails**:
   - Check storage permissions
   - Verify available disk space
   - Check camera initialization logs

4. **API Server Won't Start**:
   - Check if port 8000 is available
   - Verify FastAPI dependencies
   - Check firewall settings

### Debug Commands

```bash
# Check system status
curl http://localhost:8000/system/status

# Check camera status
curl http://localhost:8000/cameras

# Manual recording start
curl -X POST http://localhost:8000/cameras/camera1/start-recording \
  -H "Content-Type: application/json" \
  -d '{"camera_name": "camera1"}'
```

## Development

### Project Structure

```
usda_vision_system/
├── core/           # Core functionality
├── mqtt/           # MQTT client and handlers
├── camera/         # Camera management and recording
├── storage/        # File management
├── api/            # FastAPI server
└── main.py         # Application coordinator
```

### Adding New Features

1. **New Camera Type**: Extend `camera/recorder.py`
2. **New MQTT Topics**: Update `config.json` and `mqtt/handlers.py`
3. **New API Endpoints**: Add to `api/server.py`
4. **New Events**: Define in `core/events.py`

### Testing

```bash
# Run basic system test
python -c "from usda_vision_system import USDAVisionSystem; s = USDAVisionSystem(); print('OK')"

# Test MQTT connection
python -c "from usda_vision_system.mqtt.client import MQTTClient; # ... test code"

# Test camera discovery
python -c "import sys; sys.path.append('python demo'); import mvsdk; print(len(mvsdk.CameraEnumerateDevice()))"
```

## License

This project is developed for USDA research purposes.

## Support

For issues and questions:
1. Check the logs in `usda_vision_system.log`
2. Review the troubleshooting section
3. Check API status at `http://localhost:8000/health`
