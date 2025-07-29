# 🚀 USDA Vision Camera System - Complete API Documentation

This document provides comprehensive documentation for all API endpoints in the USDA Vision Camera System, including recent enhancements and new features.

## 📋 Table of Contents

- [🔧 System Status & Health](#-system-status--health)
- [📷 Camera Management](#-camera-management)
- [🎥 Recording Control](#-recording-control)
- [🤖 Auto-Recording Management](#-auto-recording-management)
- [🎛️ Camera Configuration](#️-camera-configuration)
- [📡 MQTT & Machine Status](#-mqtt--machine-status)
- [💾 Storage & File Management](#-storage--file-management)
- [🔄 Camera Recovery & Diagnostics](#-camera-recovery--diagnostics)
- [📺 Live Streaming](#-live-streaming)
- [🌐 WebSocket Real-time Updates](#-websocket-real-time-updates)

## 🔧 System Status & Health

### Get System Status
```http
GET /system/status
```
**Response**: `SystemStatusResponse`
```json
{
  "system_started": true,
  "mqtt_connected": true,
  "last_mqtt_message": "2024-01-15T10:30:00Z",
  "machines": {
    "vibratory_conveyor": {
      "name": "vibratory_conveyor",
      "state": "ON",
      "last_updated": "2024-01-15T10:30:00Z"
    }
  },
  "cameras": {
    "camera1": {
      "name": "camera1",
      "status": "ACTIVE",
      "is_recording": false,
      "auto_recording_enabled": true
    }
  },
  "active_recordings": 0,
  "total_recordings": 15,
  "uptime_seconds": 3600.5
}
```

### Health Check
```http
GET /health
```
**Response**: Simple health status
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 📷 Camera Management

### Get All Cameras
```http
GET /cameras
```
**Response**: `Dict[str, CameraStatusResponse]`

### Get Specific Camera Status
```http
GET /cameras/{camera_name}/status
```
**Response**: `CameraStatusResponse`
```json
{
  "name": "camera1",
  "status": "ACTIVE",
  "is_recording": false,
  "last_checked": "2024-01-15T10:30:00Z",
  "last_error": null,
  "device_info": {
    "model": "GigE Camera",
    "serial": "12345"
  },
  "current_recording_file": null,
  "recording_start_time": null,
  "auto_recording_enabled": true,
  "auto_recording_active": false,
  "auto_recording_failure_count": 0,
  "auto_recording_last_attempt": null,
  "auto_recording_last_error": null
}
```

## 🎥 Recording Control

### Start Recording
```http
POST /cameras/{camera_name}/start-recording
Content-Type: application/json

{
  "filename": "test_recording.avi",
  "exposure_ms": 2.0,
  "gain": 4.0,
  "fps": 5.0
}
```

**Request Model**: `StartRecordingRequest`
- `filename` (optional): Custom filename (datetime prefix will be added automatically)
- `exposure_ms` (optional): Exposure time in milliseconds
- `gain` (optional): Camera gain value
- `fps` (optional): Target frames per second

**Response**: `StartRecordingResponse`
```json
{
  "success": true,
  "message": "Recording started for camera1",
  "filename": "20240115_103000_test_recording.avi"
}
```

**Key Features**:
- ✅ **Automatic datetime prefix**: All filenames get `YYYYMMDD_HHMMSS_` prefix
- ✅ **Dynamic camera settings**: Adjust exposure, gain, and FPS per recording
- ✅ **Backward compatibility**: All existing API calls work unchanged

### Stop Recording
```http
POST /cameras/{camera_name}/stop-recording
```
**Response**: `StopRecordingResponse`
```json
{
  "success": true,
  "message": "Recording stopped for camera1",
  "duration_seconds": 45.2
}
```

## 🤖 Auto-Recording Management

### Enable Auto-Recording for Camera
```http
POST /cameras/{camera_name}/auto-recording/enable
```
**Response**: `AutoRecordingConfigResponse`
```json
{
  "success": true,
  "message": "Auto-recording enabled for camera1",
  "camera_name": "camera1",
  "enabled": true
}
```

### Disable Auto-Recording for Camera
```http
POST /cameras/{camera_name}/auto-recording/disable
```
**Response**: `AutoRecordingConfigResponse`

### Get Auto-Recording Status
```http
GET /auto-recording/status
```
**Response**: `AutoRecordingStatusResponse`
```json
{
  "running": true,
  "auto_recording_enabled": true,
  "retry_queue": {},
  "enabled_cameras": ["camera1", "camera2"]
}
```

**Auto-Recording Features**:
- 🤖 **MQTT-triggered recording**: Automatically starts/stops based on machine state
- 🔄 **Retry logic**: Failed recordings are retried with configurable delays
- 📊 **Per-camera control**: Enable/disable auto-recording individually
- 📈 **Status tracking**: Monitor failure counts and last attempts

## 🎛️ Camera Configuration

### Get Camera Configuration
```http
GET /cameras/{camera_name}/config
```
**Response**: `CameraConfigResponse`
```json
{
  "name": "camera1",
  "machine_topic": "vibratory_conveyor",
  "storage_path": "/storage/camera1",
  "enabled": true,
  "exposure_ms": 1.0,
  "gain": 3.5,
  "target_fps": 3.0,
  "auto_start_recording_enabled": true,
  "sharpness": 120,
  "contrast": 110,
  "saturation": 100,
  "gamma": 100,
  "noise_filter_enabled": true,
  "denoise_3d_enabled": false,
  "auto_white_balance": true,
  "color_temperature_preset": 0,
  "anti_flicker_enabled": true,
  "light_frequency": 1,
  "bit_depth": 8,
  "hdr_enabled": false,
  "hdr_gain_mode": 0
}
```

### Update Camera Configuration
```http
PUT /cameras/{camera_name}/config
Content-Type: application/json

{
  "exposure_ms": 2.0,
  "gain": 4.0,
  "target_fps": 5.0,
  "sharpness": 130
}
```

### Apply Configuration (Restart Required)
```http
POST /cameras/{camera_name}/apply-config
```

**Configuration Categories**:
- ✅ **Real-time**: `exposure_ms`, `gain`, `target_fps`, `sharpness`, `contrast`, etc.
- ⚠️ **Restart required**: `noise_filter_enabled`, `denoise_3d_enabled`, `bit_depth`

For detailed configuration options, see [Camera Configuration API Guide](api/CAMERA_CONFIG_API.md).

## 📡 MQTT & Machine Status

### Get All Machines
```http
GET /machines
```
**Response**: `Dict[str, MachineStatusResponse]`

### Get MQTT Status
```http
GET /mqtt/status
```
**Response**: `MQTTStatusResponse`
```json
{
  "connected": true,
  "broker_host": "192.168.1.110",
  "broker_port": 1883,
  "subscribed_topics": ["vibratory_conveyor", "blower_separator"],
  "last_message_time": "2024-01-15T10:30:00Z",
  "message_count": 1250,
  "error_count": 2,
  "uptime_seconds": 3600.5
}
```

### Get MQTT Events History
```http
GET /mqtt/events?limit=10
```
**Response**: `MQTTEventsHistoryResponse`
```json
{
  "events": [
    {
      "machine_name": "vibratory_conveyor",
      "topic": "vibratory_conveyor",
      "payload": "ON",
      "normalized_state": "ON",
      "timestamp": "2024-01-15T10:30:00Z",
      "message_number": 1250
    }
  ],
  "total_events": 1250,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

## 💾 Storage & File Management

### Get Storage Statistics
```http
GET /storage/stats
```
**Response**: `StorageStatsResponse`
```json
{
  "base_path": "/storage",
  "total_files": 150,
  "total_size_bytes": 5368709120,
  "cameras": {
    "camera1": {
      "file_count": 75,
      "total_size_bytes": 2684354560
    },
    "camera2": {
      "file_count": 75,
      "total_size_bytes": 2684354560
    }
  },
  "disk_usage": {
    "total_bytes": 107374182400,
    "used_bytes": 53687091200,
    "free_bytes": 53687091200,
    "usage_percent": 50.0
  }
}
```

### Get File List
```http
POST /storage/files
Content-Type: application/json

{
  "camera_name": "camera1",
  "start_date": "2024-01-15",
  "end_date": "2024-01-16",
  "limit": 50
}
```
**Response**: `FileListResponse`
```json
{
  "files": [
    {
      "filename": "20240115_103000_test_recording.avi",
      "camera_name": "camera1",
      "size_bytes": 52428800,
      "created_time": "2024-01-15T10:30:00Z",
      "duration_seconds": 30.5
    }
  ],
  "total_count": 1
}
```

### Cleanup Old Files
```http
POST /storage/cleanup
Content-Type: application/json

{
  "max_age_days": 30
}
```
**Response**: `CleanupResponse`
```json
{
  "files_removed": 25,
  "bytes_freed": 1073741824,
  "errors": []
}
```

## 🔄 Camera Recovery & Diagnostics

### Test Camera Connection
```http
POST /cameras/{camera_name}/test-connection
```
**Response**: `CameraTestResponse`

### Reconnect Camera
```http
POST /cameras/{camera_name}/reconnect
```
**Response**: `CameraRecoveryResponse`

### Restart Camera Grab Process
```http
POST /cameras/{camera_name}/restart-grab
```
**Response**: `CameraRecoveryResponse`

### Reset Camera Timestamp
```http
POST /cameras/{camera_name}/reset-timestamp
```
**Response**: `CameraRecoveryResponse`

### Full Camera Reset
```http
POST /cameras/{camera_name}/full-reset
```
**Response**: `CameraRecoveryResponse`

### Reinitialize Camera
```http
POST /cameras/{camera_name}/reinitialize
```
**Response**: `CameraRecoveryResponse`

**Recovery Response Example**:
```json
{
  "success": true,
  "message": "Camera camera1 reconnected successfully",
  "camera_name": "camera1",
  "operation": "reconnect",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 📺 Live Streaming

### Get Live MJPEG Stream
```http
GET /cameras/{camera_name}/stream
```
**Response**: MJPEG video stream (multipart/x-mixed-replace)

### Start Camera Stream
```http
POST /cameras/{camera_name}/start-stream
```

### Stop Camera Stream
```http
POST /cameras/{camera_name}/stop-stream
```

**Streaming Features**:
- 📺 **MJPEG format**: Compatible with web browsers and React apps
- 🔄 **Concurrent operation**: Stream while recording simultaneously
- ⚡ **Low latency**: Real-time preview for monitoring

For detailed streaming integration, see [Streaming Guide](guides/STREAMING_GUIDE.md).

## 🌐 WebSocket Real-time Updates

### Connect to WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Real-time update:', update);
};
```

**WebSocket Message Types**:
- `system_status`: System status changes
- `camera_status`: Camera status updates
- `recording_started`: Recording start events
- `recording_stopped`: Recording stop events
- `mqtt_message`: MQTT message received
- `auto_recording_event`: Auto-recording status changes

**Example WebSocket Message**:
```json
{
  "type": "recording_started",
  "data": {
    "camera_name": "camera1",
    "filename": "20240115_103000_auto_recording.avi",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🚀 Quick Start Examples

### Basic System Monitoring
```bash
# Check system health
curl http://localhost:8000/health

# Get overall system status
curl http://localhost:8000/system/status

# Get all camera statuses
curl http://localhost:8000/cameras
```

### Manual Recording Control
```bash
# Start recording with default settings
curl -X POST http://localhost:8000/cameras/camera1/start-recording \
  -H "Content-Type: application/json" \
  -d '{"filename": "manual_test.avi"}'

# Start recording with custom camera settings
curl -X POST http://localhost:8000/cameras/camera1/start-recording \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "high_quality.avi",
    "exposure_ms": 2.0,
    "gain": 4.0,
    "fps": 5.0
  }'

# Stop recording
curl -X POST http://localhost:8000/cameras/camera1/stop-recording
```

### Auto-Recording Management
```bash
# Enable auto-recording for camera1
curl -X POST http://localhost:8000/cameras/camera1/auto-recording/enable

# Check auto-recording status
curl http://localhost:8000/auto-recording/status

# Disable auto-recording for camera1
curl -X POST http://localhost:8000/cameras/camera1/auto-recording/disable
```

### Camera Configuration
```bash
# Get current camera configuration
curl http://localhost:8000/cameras/camera1/config

# Update camera settings (real-time)
curl -X PUT http://localhost:8000/cameras/camera1/config \
  -H "Content-Type: application/json" \
  -d '{
    "exposure_ms": 1.5,
    "gain": 3.0,
    "sharpness": 130,
    "contrast": 120
  }'
```

## 📈 Recent API Changes & Enhancements

### ✨ New in Latest Version

#### 1. Enhanced Recording API
- **Dynamic camera settings**: Set exposure, gain, and FPS per recording
- **Automatic datetime prefixes**: All filenames get timestamp prefixes
- **Backward compatibility**: Existing API calls work unchanged

#### 2. Auto-Recording Feature
- **Per-camera control**: Enable/disable auto-recording individually
- **MQTT integration**: Automatic recording based on machine states
- **Retry logic**: Failed recordings are automatically retried
- **Status tracking**: Monitor auto-recording attempts and failures

#### 3. Advanced Camera Configuration
- **Real-time settings**: Update exposure, gain, image quality without restart
- **Image enhancement**: Sharpness, contrast, saturation, gamma controls
- **Noise reduction**: Configurable noise filtering and 3D denoising
- **HDR support**: High Dynamic Range imaging capabilities

#### 4. Live Streaming
- **MJPEG streaming**: Real-time camera preview
- **Concurrent operation**: Stream while recording simultaneously
- **Web-compatible**: Direct integration with React/HTML video elements

#### 5. Enhanced Monitoring
- **MQTT event history**: Track machine state changes over time
- **Storage statistics**: Monitor disk usage and file counts
- **WebSocket updates**: Real-time system status notifications

### 🔄 Migration Notes

#### From Previous Versions
1. **Recording API**: All existing calls work, but now return filenames with datetime prefixes
2. **Configuration**: New camera settings are optional and backward compatible
3. **Auto-recording**: New feature, requires enabling in `config.json` and per camera

#### Configuration Updates
```json
{
  "cameras": [
    {
      "name": "camera1",
      "auto_start_recording_enabled": true,  // NEW: Enable auto-recording
      "sharpness": 120,                      // NEW: Image quality settings
      "contrast": 110,
      "saturation": 100,
      "gamma": 100,
      "noise_filter_enabled": true,
      "hdr_enabled": false
    }
  ],
  "system": {
    "auto_recording_enabled": true           // NEW: Global auto-recording toggle
  }
}
```

## 🔗 Related Documentation

- [📷 Camera Configuration API Guide](api/CAMERA_CONFIG_API.md) - Detailed camera settings
- [🤖 Auto-Recording Feature Guide](features/AUTO_RECORDING_FEATURE_GUIDE.md) - React integration
- [📺 Streaming Guide](guides/STREAMING_GUIDE.md) - Live video streaming
- [🔧 Camera Recovery Guide](guides/CAMERA_RECOVERY_GUIDE.md) - Troubleshooting
- [📡 MQTT Logging Guide](guides/MQTT_LOGGING_GUIDE.md) - MQTT configuration

## 📞 Support & Integration

### API Base URL
- **Development**: `http://localhost:8000`
- **Production**: Configure in `config.json` under `system.api_host` and `system.api_port`

### Error Handling
All endpoints return standard HTTP status codes:
- `200`: Success
- `404`: Resource not found (camera, file, etc.)
- `500`: Internal server error
- `503`: Service unavailable (camera manager, MQTT, etc.)

### Rate Limiting
- No rate limiting currently implemented
- WebSocket connections are limited to reasonable concurrent connections

### CORS Support
- CORS is enabled for web dashboard integration
- Configure allowed origins in the API server settings
```
```
