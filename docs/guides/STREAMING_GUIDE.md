# 🎥 USDA Vision Camera Live Streaming Guide

This guide explains how to use the new live preview streaming functionality that allows you to view camera feeds in real-time without blocking recording operations.

## 🌟 Key Features

- **Non-blocking streaming**: Live preview doesn't interfere with recording
- **Separate camera connections**: Streaming uses independent camera instances
- **MJPEG streaming**: Standard web-compatible video streaming
- **Multiple concurrent viewers**: Multiple browsers can view the same stream
- **REST API control**: Start/stop streaming via API endpoints
- **Web interface**: Ready-to-use HTML interface for live preview

## 🏗️ Architecture

The streaming system creates separate camera connections for preview that are independent from recording:

```
Camera Hardware
├── Recording Connection (CameraRecorder)
│   ├── Used for video file recording
│   ├── Triggered by MQTT machine states
│   └── High quality, full FPS
└── Streaming Connection (CameraStreamer)
    ├── Used for live preview
    ├── Controlled via API endpoints
    └── Optimized for web viewing (lower FPS, JPEG compression)
```

## 🚀 Quick Start

### 1. Start the System
```bash
python main.py
```

### 2. Open the Web Interface
Open `camera_preview.html` in your browser and click "Start Stream" for any camera.

### 3. API Usage
```bash
# Start streaming for camera1
curl -X POST http://localhost:8000/cameras/camera1/start-stream

# View live stream (open in browser)
http://localhost:8000/cameras/camera1/stream

# Stop streaming
curl -X POST http://localhost:8000/cameras/camera1/stop-stream
```

## 📡 API Endpoints

### Start Streaming
```http
POST /cameras/{camera_name}/start-stream
```
**Response:**
```json
{
  "success": true,
  "message": "Started streaming for camera camera1"
}
```

### Stop Streaming
```http
POST /cameras/{camera_name}/stop-stream
```
**Response:**
```json
{
  "success": true,
  "message": "Stopped streaming for camera camera1"
}
```

### Live Stream (MJPEG)
```http
GET /cameras/{camera_name}/stream
```
**Response:** Multipart MJPEG stream
**Content-Type:** `multipart/x-mixed-replace; boundary=frame`

## 🌐 Web Interface Usage

The included `camera_preview.html` provides a complete web interface:

1. **Camera Grid**: Shows all configured cameras
2. **Stream Controls**: Start/Stop/Refresh buttons for each camera
3. **Live Preview**: Real-time video feed display
4. **Status Information**: System and camera status
5. **Responsive Design**: Works on desktop and mobile

### Features:
- ✅ Real-time camera status
- ✅ One-click stream start/stop
- ✅ Automatic stream refresh
- ✅ System health monitoring
- ✅ Error handling and status messages

## 🔧 Technical Details

### Camera Streamer Configuration
- **Preview FPS**: 10 FPS (configurable)
- **JPEG Quality**: 70% (configurable)
- **Frame Buffer**: 5 frames (prevents memory buildup)
- **Timeout**: 200ms per frame capture

### Memory Management
- Automatic frame buffer cleanup
- Queue-based frame management
- Proper camera resource cleanup on stop

### Thread Safety
- Thread-safe streaming operations
- Independent from recording threads
- Proper synchronization with locks

## 🧪 Testing

### Run the Test Script
```bash
python test_streaming.py
```

This will test:
- ✅ API endpoint functionality
- ✅ Stream start/stop operations
- ✅ Concurrent recording and streaming
- ✅ Error handling

### Manual Testing
1. Start the system: `python main.py`
2. Open `camera_preview.html` in browser
3. Start streaming for a camera
4. Trigger recording via MQTT or manual API
5. Verify both work simultaneously

## 🔄 Concurrent Operations

The system supports these concurrent operations:

| Operation | Recording | Streaming | Notes |
|-----------|-----------|-----------|-------|
| Recording Only | ✅ | ❌ | Normal operation |
| Streaming Only | ❌ | ✅ | Preview without recording |
| Both Concurrent | ✅ | ✅ | **Independent connections** |

### Example: Concurrent Usage
```bash
# Start streaming
curl -X POST http://localhost:8000/cameras/camera1/start-stream

# Start recording (while streaming continues)
curl -X POST http://localhost:8000/cameras/camera1/start-recording \
  -H "Content-Type: application/json" \
  -d '{"filename": "test_recording.avi"}'

# Both operations run independently!
```

## 🛠️ Configuration

### Stream Settings (in CameraStreamer)
```python
self.preview_fps = 10.0          # Lower FPS for preview
self.preview_quality = 70        # JPEG quality (1-100)
self._frame_queue.maxsize = 5    # Frame buffer size
```

### Camera Settings
The streamer uses the same camera configuration as recording:
- Exposure time from `camera_config.exposure_ms`
- Gain from `camera_config.gain`
- Optimized trigger mode for continuous streaming

## 🚨 Important Notes

### Camera Access Patterns
- **Recording**: Blocks camera during active recording
- **Streaming**: Uses separate connection, doesn't block
- **Health Checks**: Brief, non-blocking camera tests
- **Multiple Streams**: Multiple browsers can view same stream

### Performance Considerations
- Streaming uses additional CPU/memory resources
- Lower preview FPS reduces system load
- JPEG compression reduces bandwidth usage
- Frame queue prevents memory buildup

### Error Handling
- Automatic camera resource cleanup
- Graceful handling of camera disconnections
- Stream auto-restart capabilities
- Detailed error logging

## 🔍 Troubleshooting

### Stream Not Starting
1. Check camera availability: `GET /cameras`
2. Verify camera not in error state
3. Check system logs for camera initialization errors
4. Try camera reconnection: `POST /cameras/{name}/reconnect`

### Poor Stream Quality
1. Adjust `preview_quality` setting (higher = better quality)
2. Increase `preview_fps` for smoother video
3. Check network bandwidth
4. Verify camera exposure/gain settings

### Browser Issues
1. Try different browser (Chrome/Firefox recommended)
2. Check browser console for JavaScript errors
3. Verify CORS settings in API server
4. Clear browser cache and refresh

## 📈 Future Enhancements

Potential improvements for the streaming system:

- 🔄 WebRTC support for lower latency
- 📱 Mobile app integration
- 🎛️ Real-time camera setting adjustments
- 📊 Stream analytics and monitoring
- 🔐 Authentication and access control
- 🌐 Multi-camera synchronized viewing

## 📞 Support

For issues with streaming functionality:

1. Check the system logs: `usda_vision_system.log`
2. Run the test script: `python test_streaming.py`
3. Verify API health: `http://localhost:8000/health`
4. Check camera status: `http://localhost:8000/cameras`

---

**✅ Live streaming is now ready for production use!**
