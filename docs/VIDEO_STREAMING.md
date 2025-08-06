# 🎬 Video Streaming Module

The USDA Vision Camera System now includes a modular video streaming system that provides YouTube-like video playback capabilities for your React web application.

## 🌟 Features

- **Progressive Streaming** - True chunked streaming for web browsers (no download required)
- **HTTP Range Request Support** - Enables seeking and progressive download with 206 Partial Content
- **Native MP4 Support** - Direct streaming of MP4 files optimized for web playback
- **Memory Efficient** - 8KB chunked delivery, no large file loading into memory
- **Browser Compatible** - Works with HTML5 `<video>` tag in all modern browsers
- **Intelligent Caching** - Optimized streaming performance with byte-range caching
- **Thumbnail Generation** - Extract preview images from videos
- **Modular Architecture** - Clean separation of concerns
- **No Authentication Required** - Open access for internal network use
- **CORS Enabled** - Ready for web browser integration

## 🏗️ Architecture

The video module follows clean architecture principles:

```
usda_vision_system/video/
├── domain/          # Business logic (pure Python)
├── infrastructure/  # External dependencies (OpenCV, FFmpeg)
├── application/     # Use cases and orchestration
├── presentation/    # HTTP controllers and API routes
└── integration.py   # Dependency injection and composition
```

## 🚀 API Endpoints

### List Videos
```http
GET /videos/
```
**Query Parameters:**
- `camera_name` (optional): Filter by camera name
- `start_date` (optional): Filter videos created after this date (ISO format: 2025-08-04T14:30:22)
- `end_date` (optional): Filter videos created before this date (ISO format: 2025-08-04T14:30:22)
- `limit` (optional): Maximum results (default: 50, max: 1000)
- `include_metadata` (optional): Include video metadata (default: false)

**Example Request:**
```bash
curl "http://localhost:8000/videos/?camera_name=camera1&include_metadata=true&limit=10"
```

**Response:**
```json
{
  "videos": [
    {
      "file_id": "camera1_auto_blower_separator_20250804_143022.mp4",
      "camera_name": "camera1",
      "filename": "camera1_auto_blower_separator_20250804_143022.mp4",
      "file_size_bytes": 31457280,
      "format": "mp4",
      "status": "completed",
      "created_at": "2025-08-04T14:30:22",
      "start_time": "2025-08-04T14:30:22",
      "end_time": "2025-08-04T14:32:22",
      "machine_trigger": "blower_separator",
      "is_streamable": true,
      "needs_conversion": false,
      "metadata": {
        "duration_seconds": 120.5,
        "width": 1920,
        "height": 1080,
        "fps": 30.0,
        "codec": "mp4v",
        "bitrate": 5000000,
        "aspect_ratio": 1.777
      }
    }
  ],
  "total_count": 1
}
```

### Stream Video
```http
GET /videos/{file_id}/stream
```
**Headers:**
- `Range: bytes=0-1023` (optional): Request specific byte range for seeking

**Example Requests:**
```bash
# Stream entire video (progressive streaming)
curl http://localhost:8000/videos/camera1_auto_blower_separator_20250805_123329.mp4/stream

# Stream specific byte range (for seeking)
curl -H "Range: bytes=0-1023" \
  http://localhost:8000/videos/camera1_auto_blower_separator_20250805_123329.mp4/stream
```

**Response Headers:**
- `Accept-Ranges: bytes`
- `Content-Length: {size}`
- `Content-Range: bytes {start}-{end}/{total}` (for range requests)
- `Cache-Control: public, max-age=3600`
- `Content-Type: video/mp4`

**Streaming Implementation:**
- ✅ **Progressive Streaming**: Uses FastAPI `StreamingResponse` with 8KB chunks
- ✅ **HTTP Range Requests**: Returns 206 Partial Content for seeking
- ✅ **Memory Efficient**: No large file loading, streams directly from disk
- ✅ **Browser Compatible**: Works with HTML5 `<video>` tag playback
- ✅ **Chunked Delivery**: Optimal 8KB chunk size for smooth playback
- ✅ **CORS Enabled**: Ready for web browser integration

**Response Status Codes:**
- `200 OK`: Full video streaming (progressive chunks)
- `206 Partial Content`: Range request successful
- `404 Not Found`: Video not found or not streamable
- `416 Range Not Satisfiable`: Invalid range request

### Get Video Info
```http
GET /videos/{file_id}
```
**Example Request:**
```bash
curl http://localhost:8000/videos/camera1_recording_20250804_143022.avi
```

**Response includes complete metadata:**
```json
{
  "file_id": "camera1_recording_20250804_143022.avi",
  "camera_name": "camera1",
  "filename": "camera1_recording_20250804_143022.avi",
  "file_size_bytes": 52428800,
  "format": "avi",
  "status": "completed",
  "created_at": "2025-08-04T14:30:22",
  "start_time": "2025-08-04T14:30:22",
  "end_time": "2025-08-04T14:32:22",
  "machine_trigger": "vibratory_conveyor",
  "is_streamable": true,
  "needs_conversion": true,
  "metadata": {
    "duration_seconds": 120.5,
    "width": 1920,
    "height": 1080,
    "fps": 30.0,
    "codec": "XVID",
    "bitrate": 5000000,
    "aspect_ratio": 1.777
  }
}
```

### Get Thumbnail
```http
GET /videos/{file_id}/thumbnail?timestamp=5.0&width=320&height=240
```
**Query Parameters:**
- `timestamp` (optional): Time position in seconds to extract thumbnail from (default: 1.0)
- `width` (optional): Thumbnail width in pixels (default: 320)
- `height` (optional): Thumbnail height in pixels (default: 240)

**Example Request:**
```bash
curl "http://localhost:8000/videos/camera1_recording_20250804_143022.avi/thumbnail?timestamp=5.0&width=320&height=240" \
  --output thumbnail.jpg
```

**Response**: JPEG image data with caching headers
- `Content-Type: image/jpeg`
- `Cache-Control: public, max-age=3600`

### Streaming Info
```http
GET /videos/{file_id}/info
```
**Example Request:**
```bash
curl http://localhost:8000/videos/camera1_recording_20250804_143022.avi/info
```

**Response**: Technical streaming details
```json
{
  "file_id": "camera1_recording_20250804_143022.avi",
  "file_size_bytes": 52428800,
  "content_type": "video/x-msvideo",
  "supports_range_requests": true,
  "chunk_size_bytes": 262144
}
```

### Video Validation
```http
POST /videos/{file_id}/validate
```
**Example Request:**
```bash
curl -X POST http://localhost:8000/videos/camera1_recording_20250804_143022.avi/validate
```

**Response**: Validation status
```json
{
  "file_id": "camera1_recording_20250804_143022.avi",
  "is_valid": true
}
```

### Cache Management
```http
POST /videos/{file_id}/cache/invalidate
```
**Example Request:**
```bash
curl -X POST http://localhost:8000/videos/camera1_recording_20250804_143022.avi/cache/invalidate
```

**Response**: Cache invalidation status
```json
{
  "file_id": "camera1_recording_20250804_143022.avi",
  "cache_invalidated": true
}
```

### Admin: Cache Cleanup
```http
POST /admin/videos/cache/cleanup?max_size_mb=100
```
**Example Request:**
```bash
curl -X POST "http://localhost:8000/admin/videos/cache/cleanup?max_size_mb=100"
```

**Response**: Cache cleanup results
```json
{
  "cache_cleaned": true,
  "entries_removed": 15,
  "max_size_mb": 100
}
```

## 🌐 React Integration

### Basic Video Player
```jsx
function VideoPlayer({ fileId }) {
  return (
    <video
      controls
      width="100%"
      preload="metadata"
      style={{ maxWidth: '800px' }}
    >
      <source
        src={`${API_BASE_URL}/videos/${fileId}/stream`}
        type="video/mp4"
      />
      Your browser does not support video playback.
    </video>
  );
}
```

### Advanced Player with Thumbnail
```jsx
function VideoPlayerWithThumbnail({ fileId }) {
  const [thumbnail, setThumbnail] = useState(null);
  
  useEffect(() => {
    fetch(`${API_BASE_URL}/videos/${fileId}/thumbnail`)
      .then(response => response.blob())
      .then(blob => setThumbnail(URL.createObjectURL(blob)));
  }, [fileId]);
  
  return (
    <video controls width="100%" poster={thumbnail}>
      <source 
        src={`${API_BASE_URL}/videos/${fileId}/stream`} 
        type="video/mp4" 
      />
    </video>
  );
}
```

### Video List Component
```jsx
function VideoList({ cameraName }) {
  const [videos, setVideos] = useState([]);
  
  useEffect(() => {
    const params = new URLSearchParams();
    if (cameraName) params.append('camera_name', cameraName);
    params.append('include_metadata', 'true');
    
    fetch(`${API_BASE_URL}/videos/?${params}`)
      .then(response => response.json())
      .then(data => setVideos(data.videos));
  }, [cameraName]);
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {videos.map(video => (
        <VideoCard key={video.file_id} video={video} />
      ))}
    </div>
  );
}
```

## 🔧 Configuration

The video module is automatically initialized when the API server starts. Configuration options:

```python
# In your API server initialization
video_module = create_video_module(
    config=config,
    storage_manager=storage_manager,
    enable_caching=True,      # Enable streaming cache
    enable_conversion=True    # Enable format conversion
)
```

### Configuration Parameters
- **`enable_caching`**: Enable/disable intelligent byte-range caching (default: True)
- **`cache_size_mb`**: Maximum cache size in MB (default: 100)
- **`cache_max_age_minutes`**: Cache entry expiration time (default: 30)
- **`enable_conversion`**: Enable/disable automatic AVI to MP4 conversion (default: True)
- **`conversion_quality`**: Video conversion quality: "low", "medium", "high" (default: "medium")

### System Requirements
- **OpenCV**: Required for thumbnail generation and metadata extraction
- **FFmpeg**: Optional, for video format conversion (graceful fallback if not available)
- **Storage**: Sufficient disk space for video files and cache
- **Memory**: Recommended 2GB+ RAM for caching and video processing

## 🔐 Authentication & Security

### Current Security Model
**⚠️ IMPORTANT: No authentication is currently implemented.**

- **Open Access**: All video streaming endpoints are publicly accessible
- **CORS Policy**: Currently set to allow all origins (`allow_origins=["*"]`)
- **Network Security**: Designed for internal network use only
- **No API Keys**: No authentication tokens or API keys required
- **No Rate Limiting**: No request rate limiting currently implemented

### Security Considerations for Production

#### For Internal Network Deployment
```bash
# Current configuration is suitable for:
# - Internal corporate networks
# - Isolated network segments
# - Development and testing environments
```

#### For External Access (Recommendations)
If you need to expose the video streaming API externally, consider implementing:

1. **Authentication Layer**
   ```python
   # Example: Add JWT authentication
   from fastapi import Depends, HTTPException
   from fastapi.security import HTTPBearer

   security = HTTPBearer()

   async def verify_token(token: str = Depends(security)):
       # Implement token verification logic
       pass
   ```

2. **CORS Configuration**
   ```python
   # Restrict CORS to specific domains
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"]
   )
   ```

3. **Rate Limiting**
   ```python
   # Example: Add rate limiting
   from slowapi import Limiter

   limiter = Limiter(key_func=get_remote_address)

   @app.get("/videos/")
   @limiter.limit("10/minute")
   async def list_videos():
       pass
   ```

4. **Network Security**
   - Use HTTPS/TLS for encrypted communication
   - Implement firewall rules to restrict access
   - Consider VPN access for remote users
   - Use reverse proxy (nginx) for additional security

### Access Control Summary
```
┌─────────────────────────────────────────────────────────────┐
│                    Current Access Model                     │
├─────────────────────────────────────────────────────────────┤
│ Authentication:     ❌ None                                 │
│ Authorization:      ❌ None                                 │
│ CORS:              ✅ Enabled (all origins)                │
│ Rate Limiting:      ❌ None                                 │
│ HTTPS:             ⚠️  Depends on deployment               │
│ Network Security:   ⚠️  Firewall/VPN recommended           │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Performance

- **Caching**: Intelligent byte-range caching reduces disk I/O
- **Adaptive Chunking**: Optimal chunk sizes based on file size
- **Range Requests**: Only download needed portions
- **Format Conversion**: Automatic conversion to web-compatible formats

## 🛠️ Service Management

### Restart Service
```bash
sudo systemctl restart usda-vision-camera
```

### Check Status
```bash
# Check video module status
curl http://localhost:8000/system/video-module

# Check available videos
curl http://localhost:8000/videos/
```

### Logs
```bash
sudo journalctl -u usda-vision-camera -f
```

## 🧪 Testing

Run the video module tests:
```bash
cd /home/alireza/USDA-vision-cameras
PYTHONPATH=/home/alireza/USDA-vision-cameras python tests/test_video_module.py
```

## 🔍 Troubleshooting

### Video Not Playing
1. **Check if file exists**: `GET /videos/{file_id}`
   ```bash
   curl http://localhost:8000/videos/camera1_recording_20250804_143022.avi
   ```
2. **Verify streaming info**: `GET /videos/{file_id}/info`
   ```bash
   curl http://localhost:8000/videos/camera1_recording_20250804_143022.avi/info
   ```
3. **Test direct stream**: `GET /videos/{file_id}/stream`
   ```bash
   curl -I http://localhost:8000/videos/camera1_recording_20250804_143022.avi/stream
   ```
4. **Validate video file**: `POST /videos/{file_id}/validate`
   ```bash
   curl -X POST http://localhost:8000/videos/camera1_recording_20250804_143022.avi/validate
   ```

### Performance Issues
1. **Check cache status**: Clean up cache if needed
   ```bash
   curl -X POST "http://localhost:8000/admin/videos/cache/cleanup?max_size_mb=100"
   ```
2. **Monitor system resources**: Check CPU, memory, and disk usage
3. **Adjust cache size**: Modify configuration parameters
4. **Invalidate specific cache**: For updated files
   ```bash
   curl -X POST http://localhost:8000/videos/{file_id}/cache/invalidate
   ```

### Format Issues
- **AVI files**: Automatically converted to MP4 for web compatibility
- **Conversion requires FFmpeg**: Optional dependency with graceful fallback
- **Supported formats**: AVI (with conversion), MP4 (native), WebM (native)

### Common HTTP Status Codes
- **200**: Success - Video streamed successfully
- **206**: Partial Content - Range request successful
- **404**: Not Found - Video file doesn't exist or isn't streamable
- **416**: Range Not Satisfiable - Invalid range request
- **500**: Internal Server Error - Failed to read video data or generate thumbnail

### Browser Compatibility
- **Chrome/Chromium**: Full support for MP4 and range requests
- **Firefox**: Full support for MP4 and range requests
- **Safari**: Full support for MP4 and range requests
- **Edge**: Full support for MP4 and range requests
- **Mobile browsers**: Generally good support for MP4 streaming

### Error Scenarios and Solutions

#### Video File Issues
```bash
# Problem: Video not found (404)
curl http://localhost:8000/videos/nonexistent_video.mp4
# Response: {"detail": "Video nonexistent_video.mp4 not found"}
# Solution: Verify file_id exists using list endpoint

# Problem: Video not streamable
curl http://localhost:8000/videos/corrupted_video.avi/stream
# Response: {"detail": "Video corrupted_video.avi not found or not streamable"}
# Solution: Use validation endpoint to check file integrity
```

#### Range Request Issues
```bash
# Problem: Invalid range request (416)
curl -H "Range: bytes=999999999-" http://localhost:8000/videos/small_video.mp4/stream
# Response: {"detail": "Invalid range request: Range exceeds file size"}
# Solution: Check file size first using /info endpoint

# Problem: Malformed range header
curl -H "Range: invalid-range" http://localhost:8000/videos/video.mp4/stream
# Response: {"detail": "Invalid range request: Malformed range header"}
# Solution: Use proper range format: "bytes=start-end"
```

#### Thumbnail Generation Issues
```bash
# Problem: Thumbnail generation failed (404)
curl http://localhost:8000/videos/audio_only.mp4/thumbnail
# Response: {"detail": "Could not generate thumbnail for audio_only.mp4"}
# Solution: Verify video has visual content and is not audio-only

# Problem: Invalid timestamp
curl "http://localhost:8000/videos/short_video.mp4/thumbnail?timestamp=999"
# Response: Returns thumbnail from last available frame
# Solution: Check video duration first using metadata
```

#### System Resource Issues
```bash
# Problem: Cache full or system overloaded (500)
curl http://localhost:8000/videos/large_video.mp4/stream
# Response: {"detail": "Failed to read video data"}
# Solution: Clean cache or wait for system resources
curl -X POST "http://localhost:8000/admin/videos/cache/cleanup?max_size_mb=50"
```

### Debugging Workflow
```bash
# Step 1: Check system health
curl http://localhost:8000/health

# Step 2: Verify video exists and get info
curl http://localhost:8000/videos/your_video_id

# Step 3: Check streaming capabilities
curl http://localhost:8000/videos/your_video_id/info

# Step 4: Validate video file
curl -X POST http://localhost:8000/videos/your_video_id/validate

# Step 5: Test basic streaming
curl -I http://localhost:8000/videos/your_video_id/stream

# Step 6: Test range request
curl -I -H "Range: bytes=0-1023" http://localhost:8000/videos/your_video_id/stream
```

### Performance Monitoring
```bash
# Monitor cache usage
curl -X POST "http://localhost:8000/admin/videos/cache/cleanup?max_size_mb=100"

# Check system resources
curl http://localhost:8000/system/status

# Monitor video module status
curl http://localhost:8000/videos/ | jq '.total_count'
```

## 🎯 Next Steps

1. **Restart the usda-vision-camera service** to enable video streaming
2. **Test the endpoints** using curl or your browser
3. **Integrate with your React app** using the provided examples
4. **Monitor performance** and adjust caching as needed

The video streaming system is now ready for production use! 🚀
