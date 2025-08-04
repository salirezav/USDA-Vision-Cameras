# 🎬 Video Streaming Module

The USDA Vision Camera System now includes a modular video streaming system that provides YouTube-like video playback capabilities for your React web application.

## 🌟 Features

- **HTTP Range Request Support** - Enables seeking and progressive download
- **Native MP4 Support** - Direct streaming of MP4 files with automatic AVI conversion
- **Intelligent Caching** - Optimized streaming performance
- **Thumbnail Generation** - Extract preview images from videos
- **Modular Architecture** - Clean separation of concerns

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
- `camera_name` - Filter by camera
- `start_date` - Filter by date range
- `end_date` - Filter by date range  
- `limit` - Maximum results (default: 50)
- `include_metadata` - Include video metadata

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
      "is_streamable": true,
      "needs_conversion": true
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
- `Range: bytes=0-1023` - Request specific byte range

**Features:**
- Supports HTTP range requests for seeking
- Returns 206 Partial Content for range requests
- Automatic format conversion for web compatibility
- Intelligent caching for performance

### Get Video Info
```http
GET /videos/{file_id}
```
**Response includes metadata:**
```json
{
  "file_id": "camera1_recording_20250804_143022.avi",
  "metadata": {
    "duration_seconds": 120.5,
    "width": 1920,
    "height": 1080,
    "fps": 30.0,
    "codec": "XVID",
    "aspect_ratio": 1.777
  }
}
```

### Get Thumbnail
```http
GET /videos/{file_id}/thumbnail?timestamp=5.0&width=320&height=240
```
Returns JPEG thumbnail image.

### Streaming Info
```http
GET /videos/{file_id}/info
```
Returns technical streaming details:
```json
{
  "file_id": "camera1_recording_20250804_143022.avi",
  "file_size_bytes": 52428800,
  "content_type": "video/x-msvideo",
  "supports_range_requests": true,
  "chunk_size_bytes": 262144
}
```

## 🌐 React Integration

### Basic Video Player
```jsx
function VideoPlayer({ fileId }) {
  return (
    <video controls width="100%">
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
1. Check if file exists: `GET /videos/{file_id}`
2. Verify streaming info: `GET /videos/{file_id}/info`
3. Test direct stream: `GET /videos/{file_id}/stream`

### Performance Issues
1. Check cache status: `GET /admin/videos/cache/cleanup`
2. Monitor system resources
3. Adjust cache size in configuration

### Format Issues
- AVI files are automatically converted to MP4 for web compatibility
- Conversion requires FFmpeg (optional, graceful fallback)

## 🎯 Next Steps

1. **Restart the usda-vision-camera service** to enable video streaming
2. **Test the endpoints** using curl or your browser
3. **Integrate with your React app** using the provided examples
4. **Monitor performance** and adjust caching as needed

The video streaming system is now ready for production use! 🚀
