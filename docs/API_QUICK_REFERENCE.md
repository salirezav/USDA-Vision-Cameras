# 🚀 USDA Vision Camera System - API Quick Reference

Quick reference for the most commonly used API endpoints. For complete documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## 🔧 System Status

```bash
# Health check
curl http://localhost:8000/health

# System overview
curl http://localhost:8000/system/status

# All cameras
curl http://localhost:8000/cameras

# All machines
curl http://localhost:8000/machines
```

## 🎥 Recording Control

### Start Recording (Basic)
```bash
curl -X POST http://localhost:8000/cameras/camera1/start-recording \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.avi"}'
```

### Start Recording (With Settings)
```bash
curl -X POST http://localhost:8000/cameras/camera1/start-recording \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "high_quality.avi",
    "exposure_ms": 2.0,
    "gain": 4.0,
    "fps": 5.0
  }'
```

### Stop Recording
```bash
curl -X POST http://localhost:8000/cameras/camera1/stop-recording
```

## 🤖 Auto-Recording

```bash
# Enable auto-recording
curl -X POST http://localhost:8000/cameras/camera1/auto-recording/enable

# Disable auto-recording
curl -X POST http://localhost:8000/cameras/camera1/auto-recording/disable

# Check auto-recording status
curl http://localhost:8000/auto-recording/status
```

## 🎛️ Camera Configuration

```bash
# Get camera config
curl http://localhost:8000/cameras/camera1/config

# Update camera settings
curl -X PUT http://localhost:8000/cameras/camera1/config \
  -H "Content-Type: application/json" \
  -d '{
    "exposure_ms": 1.5,
    "gain": 3.0,
    "sharpness": 130
  }'
```

## 📺 Live Streaming

```bash
# Start streaming
curl -X POST http://localhost:8000/cameras/camera1/start-stream

# Get MJPEG stream (use in browser/video element)
# http://localhost:8000/cameras/camera1/stream

# Stop streaming
curl -X POST http://localhost:8000/cameras/camera1/stop-stream
```

## 🔄 Camera Recovery

```bash
# Test connection
curl -X POST http://localhost:8000/cameras/camera1/test-connection

# Reconnect camera
curl -X POST http://localhost:8000/cameras/camera1/reconnect

# Full reset
curl -X POST http://localhost:8000/cameras/camera1/full-reset
```

## 💾 Storage Management

```bash
# Storage statistics
curl http://localhost:8000/storage/stats

# List files
curl -X POST http://localhost:8000/storage/files \
  -H "Content-Type: application/json" \
  -d '{"camera_name": "camera1", "limit": 10}'

# Cleanup old files
curl -X POST http://localhost:8000/storage/cleanup \
  -H "Content-Type: application/json" \
  -d '{"max_age_days": 30}'
```

## 📡 MQTT Monitoring

```bash
# MQTT status
curl http://localhost:8000/mqtt/status

# Recent MQTT events
curl http://localhost:8000/mqtt/events?limit=10
```

## 🌐 WebSocket Connection

```javascript
// Connect to real-time updates
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Update:', update);
};
```

## 📊 Response Examples

### System Status Response
```json
{
  "system_started": true,
  "mqtt_connected": true,
  "cameras": {
    "camera1": {
      "name": "camera1",
      "status": "ACTIVE",
      "is_recording": false,
      "auto_recording_enabled": true
    }
  },
  "active_recordings": 0,
  "total_recordings": 15
}
```

### Recording Start Response
```json
{
  "success": true,
  "message": "Recording started for camera1",
  "filename": "20240115_103000_test.avi"
}
```

### Camera Status Response
```json
{
  "name": "camera1",
  "status": "ACTIVE",
  "is_recording": false,
  "auto_recording_enabled": true,
  "auto_recording_active": false,
  "auto_recording_failure_count": 0
}
```

## 🔗 Related Documentation

- [📚 Complete API Documentation](API_DOCUMENTATION.md)
- [🎛️ Camera Configuration Guide](api/CAMERA_CONFIG_API.md)
- [🤖 Auto-Recording Feature Guide](features/AUTO_RECORDING_FEATURE_GUIDE.md)
- [📺 Streaming Guide](guides/STREAMING_GUIDE.md)

## 💡 Tips

- All filenames automatically get datetime prefixes: `YYYYMMDD_HHMMSS_`
- Camera settings can be updated in real-time during recording
- Auto-recording is controlled per camera and globally
- WebSocket provides real-time updates for dashboard integration
- CORS is enabled for web application integration
