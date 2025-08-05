# 🤖 Web AI Agent - Video Integration Guide

This guide provides the essential information for integrating USDA Vision Camera video streaming into your web application.

## 🎯 Quick Start

### Video Streaming Status: ✅ READY
- **Progressive streaming implemented** - Videos play in browsers (no download)
- **86 MP4 files available** - All properly indexed and streamable
- **HTTP range requests supported** - Seeking and progressive playback work
- **Memory efficient** - 8KB chunked delivery

## 🚀 API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. List Available Videos
```http
GET /videos/?camera_name={camera}&limit={limit}
```

**Example:**
```bash
curl "http://localhost:8000/videos/?camera_name=camera1&limit=10"
```

**Response:**
```json
{
  "videos": [
    {
      "file_id": "camera1_auto_blower_separator_20250805_123329.mp4",
      "camera_name": "camera1",
      "file_size_bytes": 1072014489,
      "format": "mp4",
      "status": "completed",
      "is_streamable": true,
      "created_at": "2025-08-05T12:43:12.631210"
    }
  ],
  "total_count": 1
}
```

### 2. Stream Video (Progressive)
```http
GET /videos/{file_id}/stream
```

**Example:**
```bash
curl "http://localhost:8000/videos/camera1_auto_blower_separator_20250805_123329.mp4/stream"
```

**Features:**
- ✅ Progressive streaming (8KB chunks)
- ✅ HTTP range requests (206 Partial Content)
- ✅ Browser compatible (HTML5 video)
- ✅ Seeking support
- ✅ No authentication required

### 3. Get Video Thumbnail
```http
GET /videos/{file_id}/thumbnail?timestamp={seconds}&width={px}&height={px}
```

**Example:**
```bash
curl "http://localhost:8000/videos/camera1_auto_blower_separator_20250805_123329.mp4/thumbnail?timestamp=5.0&width=320&height=240"
```

## 🌐 Web Integration

### HTML5 Video Player
```html
<video controls width="100%" preload="metadata">
  <source src="http://localhost:8000/videos/{file_id}/stream" type="video/mp4">
  Your browser does not support video playback.
</video>
```

### React Component
```jsx
function VideoPlayer({ fileId, width = "100%" }) {
  const streamUrl = `http://localhost:8000/videos/${fileId}/stream`;
  const thumbnailUrl = `http://localhost:8000/videos/${fileId}/thumbnail`;
  
  return (
    <video 
      controls 
      width={width}
      preload="metadata"
      poster={thumbnailUrl}
      style={{ maxWidth: '800px', borderRadius: '8px' }}
    >
      <source src={streamUrl} type="video/mp4" />
      Your browser does not support video playback.
    </video>
  );
}
```

### Video List Component
```jsx
function VideoList({ cameraName = null, limit = 20 }) {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const params = new URLSearchParams();
    if (cameraName) params.append('camera_name', cameraName);
    params.append('limit', limit.toString());
    
    fetch(`http://localhost:8000/videos/?${params}`)
      .then(response => response.json())
      .then(data => {
        // Filter only streamable MP4 videos
        const streamableVideos = data.videos.filter(
          v => v.format === 'mp4' && v.is_streamable
        );
        setVideos(streamableVideos);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error loading videos:', error);
        setLoading(false);
      });
  }, [cameraName, limit]);
  
  if (loading) return <div>Loading videos...</div>;
  
  return (
    <div className="video-grid">
      {videos.map(video => (
        <div key={video.file_id} className="video-card">
          <h3>{video.file_id}</h3>
          <p>Camera: {video.camera_name}</p>
          <p>Size: {(video.file_size_bytes / 1024 / 1024).toFixed(1)} MB</p>
          <VideoPlayer fileId={video.file_id} width="100%" />
        </div>
      ))}
    </div>
  );
}
```

## 📊 Available Data

### Current Video Inventory
- **Total Videos**: 161 files
- **MP4 Files**: 86 (all streamable ✅)
- **AVI Files**: 75 (legacy format, not prioritized)
- **Cameras**: camera1, camera2
- **Date Range**: July 29 - August 5, 2025

### Video File Naming Convention
```
{camera}_{trigger}_{machine}_{YYYYMMDD}_{HHMMSS}.mp4
```

**Examples:**
- `camera1_auto_blower_separator_20250805_123329.mp4`
- `camera2_auto_vibratory_conveyor_20250805_123042.mp4`
- `20250804_161305_manual_camera1_2025-08-04T20-13-09-634Z.mp4`

### Machine Triggers
- `auto_blower_separator` - Automatic recording triggered by blower separator
- `auto_vibratory_conveyor` - Automatic recording triggered by vibratory conveyor  
- `manual` - Manual recording initiated by user

## 🔧 Technical Details

### Streaming Implementation
- **Method**: FastAPI `StreamingResponse` with async generators
- **Chunk Size**: 8KB for optimal performance
- **Range Requests**: Full HTTP/1.1 range request support
- **Status Codes**: 200 (full), 206 (partial), 404 (not found)
- **CORS**: Enabled for all origins
- **Caching**: Server-side byte-range caching

### Browser Compatibility
- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers

### Performance Characteristics
- **Memory Usage**: Low (8KB chunks, no large file loading)
- **Seeking**: Instant (HTTP range requests)
- **Startup Time**: Fast (metadata preload)
- **Bandwidth**: Adaptive (only downloads viewed portions)

## 🛠️ Error Handling

### Common Scenarios
```javascript
// Check if video is streamable
const checkVideo = async (fileId) => {
  try {
    const response = await fetch(`http://localhost:8000/videos/${fileId}`);
    const video = await response.json();
    
    if (!video.is_streamable) {
      console.warn(`Video ${fileId} is not streamable`);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error(`Error checking video ${fileId}:`, error);
    return false;
  }
};

// Handle video loading errors
const VideoPlayerWithErrorHandling = ({ fileId }) => {
  const [error, setError] = useState(null);
  
  const handleError = (e) => {
    console.error('Video playback error:', e);
    setError('Failed to load video. Please try again.');
  };
  
  if (error) {
    return <div className="error">❌ {error}</div>;
  }
  
  return (
    <video 
      controls 
      onError={handleError}
      src={`http://localhost:8000/videos/${fileId}/stream`}
    />
  );
};
```

### HTTP Status Codes
- `200 OK` - Video streaming successfully
- `206 Partial Content` - Range request successful  
- `404 Not Found` - Video not found or not streamable
- `416 Range Not Satisfiable` - Invalid range request
- `500 Internal Server Error` - Server error reading video

## 🔐 Security Notes

### Current Configuration
- **Authentication**: None (open access)
- **CORS**: Enabled for all origins
- **Network**: Designed for internal use
- **HTTPS**: Not required (HTTP works)

### For Production Use
Consider implementing:
- Authentication/authorization
- Rate limiting
- HTTPS/TLS encryption
- Network access controls

## 🧪 Testing

### Quick Test
```bash
# Test video listing
curl "http://localhost:8000/videos/?limit=5"

# Test video streaming
curl -I "http://localhost:8000/videos/camera1_auto_blower_separator_20250805_123329.mp4/stream"

# Test range request
curl -H "Range: bytes=0-1023" "http://localhost:8000/videos/camera1_auto_blower_separator_20250805_123329.mp4/stream" -o test_chunk.mp4
```

### Browser Test
Open: `file:///home/alireza/USDA-vision-cameras/test_video_streaming.html`

## 📞 Support

### Service Management
```bash
# Restart video service
sudo systemctl restart usda-vision-camera

# Check service status
sudo systemctl status usda-vision-camera

# View logs
sudo journalctl -u usda-vision-camera -f
```

### Health Check
```bash
curl http://localhost:8000/health
```

---

**✅ Ready for Integration**: The video streaming system is fully operational and ready for web application integration. All MP4 files are streamable with progressive playback support.
