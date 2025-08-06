# 🤖 AI Agent Video Integration Guide

This guide provides comprehensive step-by-step instructions for AI agents and external systems to successfully integrate with the USDA Vision Camera System's video streaming functionality.

## 🎯 Overview

The USDA Vision Camera System provides a complete video streaming API that allows AI agents to:
- Browse and select videos from multiple cameras
- Stream videos with seeking capabilities
- Generate thumbnails for preview
- Access video metadata and technical information

## 🔗 API Base Configuration

### Connection Details
```bash
# Default API Base URL
API_BASE_URL="http://localhost:8000"

# For remote access, replace with actual server IP/hostname
API_BASE_URL="http://192.168.1.100:8000"
```

### Authentication
**⚠️ IMPORTANT: No authentication is currently required.**
- All endpoints are publicly accessible
- No API keys or tokens needed
- CORS is enabled for web browser integration

## 📋 Step-by-Step Integration Workflow

### Step 1: Verify System Connectivity
```bash
# Test basic connectivity
curl -f "${API_BASE_URL}/health" || echo "❌ System not accessible"

# Check system status
curl "${API_BASE_URL}/system/status"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-05T10:30:00Z"
}
```

### Step 2: List Available Videos
```bash
# Get all videos with metadata
curl "${API_BASE_URL}/videos/?include_metadata=true&limit=50"

# Filter by specific camera
curl "${API_BASE_URL}/videos/?camera_name=camera1&include_metadata=true"

# Filter by date range
curl "${API_BASE_URL}/videos/?start_date=2025-08-04T00:00:00&end_date=2025-08-05T23:59:59"
```

**Response Structure:**
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

### Step 3: Select and Validate Video
```bash
# Get detailed video information
FILE_ID="camera1_auto_blower_separator_20250804_143022.mp4"
curl "${API_BASE_URL}/videos/${FILE_ID}"

# Validate video is playable
curl -X POST "${API_BASE_URL}/videos/${FILE_ID}/validate"

# Get streaming technical details
curl "${API_BASE_URL}/videos/${FILE_ID}/info"
```

### Step 4: Generate Video Thumbnail
```bash
# Generate thumbnail at 5 seconds, 320x240 resolution
curl "${API_BASE_URL}/videos/${FILE_ID}/thumbnail?timestamp=5.0&width=320&height=240" \
  --output "thumbnail_${FILE_ID}.jpg"

# Generate multiple thumbnails for preview
for timestamp in 1 30 60 90; do
  curl "${API_BASE_URL}/videos/${FILE_ID}/thumbnail?timestamp=${timestamp}&width=160&height=120" \
    --output "preview_${timestamp}s.jpg"
done
```

### Step 5: Stream Video Content
```bash
# Stream entire video
curl "${API_BASE_URL}/videos/${FILE_ID}/stream" --output "video.mp4"

# Stream specific byte range (for seeking)
curl -H "Range: bytes=0-1048575" \
  "${API_BASE_URL}/videos/${FILE_ID}/stream" \
  --output "video_chunk.mp4"

# Test range request support
curl -I -H "Range: bytes=0-1023" \
  "${API_BASE_URL}/videos/${FILE_ID}/stream"
```

## 🔧 Programming Language Examples

### Python Integration
```python
import requests
import json
from typing import List, Dict, Optional

class USDAVideoClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def list_videos(self, camera_name: Optional[str] = None, 
                   include_metadata: bool = True, limit: int = 50) -> Dict:
        """List available videos with optional filtering."""
        params = {
            'include_metadata': include_metadata,
            'limit': limit
        }
        if camera_name:
            params['camera_name'] = camera_name
        
        response = self.session.get(f"{self.base_url}/videos/", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_video_info(self, file_id: str) -> Dict:
        """Get detailed video information."""
        response = self.session.get(f"{self.base_url}/videos/{file_id}")
        response.raise_for_status()
        return response.json()
    
    def get_thumbnail(self, file_id: str, timestamp: float = 1.0, 
                     width: int = 320, height: int = 240) -> bytes:
        """Generate and download video thumbnail."""
        params = {
            'timestamp': timestamp,
            'width': width,
            'height': height
        }
        response = self.session.get(
            f"{self.base_url}/videos/{file_id}/thumbnail", 
            params=params
        )
        response.raise_for_status()
        return response.content
    
    def stream_video_range(self, file_id: str, start_byte: int, 
                          end_byte: int) -> bytes:
        """Stream specific byte range of video."""
        headers = {'Range': f'bytes={start_byte}-{end_byte}'}
        response = self.session.get(
            f"{self.base_url}/videos/{file_id}/stream",
            headers=headers
        )
        response.raise_for_status()
        return response.content
    
    def validate_video(self, file_id: str) -> bool:
        """Validate that video is accessible and playable."""
        response = self.session.post(f"{self.base_url}/videos/{file_id}/validate")
        response.raise_for_status()
        return response.json().get('is_valid', False)

# Usage example
client = USDAVideoClient("http://192.168.1.100:8000")

# List videos from camera1
videos = client.list_videos(camera_name="camera1")
print(f"Found {videos['total_count']} videos")

# Select first video
if videos['videos']:
    video = videos['videos'][0]
    file_id = video['file_id']
    
    # Validate video
    if client.validate_video(file_id):
        print(f"✅ Video {file_id} is valid")
        
        # Get thumbnail
        thumbnail = client.get_thumbnail(file_id, timestamp=5.0)
        with open(f"thumbnail_{file_id}.jpg", "wb") as f:
            f.write(thumbnail)
        
        # Stream first 1MB
        chunk = client.stream_video_range(file_id, 0, 1048575)
        print(f"Downloaded {len(chunk)} bytes")
```

### JavaScript/Node.js Integration
```javascript
class USDAVideoClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl.replace(/\/$/, '');
    }
    
    async listVideos(options = {}) {
        const params = new URLSearchParams({
            include_metadata: options.includeMetadata || true,
            limit: options.limit || 50
        });
        
        if (options.cameraName) {
            params.append('camera_name', options.cameraName);
        }
        
        const response = await fetch(`${this.baseUrl}/videos/?${params}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    }
    
    async getVideoInfo(fileId) {
        const response = await fetch(`${this.baseUrl}/videos/${fileId}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    }
    
    async getThumbnail(fileId, options = {}) {
        const params = new URLSearchParams({
            timestamp: options.timestamp || 1.0,
            width: options.width || 320,
            height: options.height || 240
        });
        
        const response = await fetch(
            `${this.baseUrl}/videos/${fileId}/thumbnail?${params}`
        );
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.blob();
    }
    
    async validateVideo(fileId) {
        const response = await fetch(
            `${this.baseUrl}/videos/${fileId}/validate`,
            { method: 'POST' }
        );
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        return result.is_valid;
    }
    
    getStreamUrl(fileId) {
        return `${this.baseUrl}/videos/${fileId}/stream`;
    }
}

// Usage example
const client = new USDAVideoClient('http://192.168.1.100:8000');

async function integrateWithVideos() {
    try {
        // List videos
        const videos = await client.listVideos({ cameraName: 'camera1' });
        console.log(`Found ${videos.total_count} videos`);
        
        if (videos.videos.length > 0) {
            const video = videos.videos[0];
            const fileId = video.file_id;
            
            // Validate video
            const isValid = await client.validateVideo(fileId);
            if (isValid) {
                console.log(`✅ Video ${fileId} is valid`);
                
                // Get thumbnail
                const thumbnail = await client.getThumbnail(fileId, {
                    timestamp: 5.0,
                    width: 320,
                    height: 240
                });
                
                // Create video element for playback
                const videoElement = document.createElement('video');
                videoElement.controls = true;
                videoElement.src = client.getStreamUrl(fileId);
                document.body.appendChild(videoElement);
            }
        }
    } catch (error) {
        console.error('Integration error:', error);
    }
}
```

## 🚨 Error Handling

### Common HTTP Status Codes
```bash
# Success responses
200  # OK - Request successful
206  # Partial Content - Range request successful

# Client error responses  
400  # Bad Request - Invalid parameters
404  # Not Found - Video file doesn't exist
416  # Range Not Satisfiable - Invalid range request

# Server error responses
500  # Internal Server Error - Failed to process video
503  # Service Unavailable - Video module not available
```

### Error Response Format
```json
{
  "detail": "Video camera1_recording_20250804_143022.avi not found"
}
```

### Robust Error Handling Example
```python
def safe_video_operation(client, file_id):
    try:
        # Validate video first
        if not client.validate_video(file_id):
            return {"error": "Video is not valid or accessible"}
        
        # Get video info
        video_info = client.get_video_info(file_id)
        
        # Check if streamable
        if not video_info.get('is_streamable', False):
            return {"error": "Video is not streamable"}
        
        return {"success": True, "video_info": video_info}
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"error": "Video not found"}
        elif e.response.status_code == 416:
            return {"error": "Invalid range request"}
        else:
            return {"error": f"HTTP error: {e.response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to video server"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
```

## ✅ Integration Checklist

### Pre-Integration
- [ ] Verify network connectivity to USDA Vision Camera System
- [ ] Test basic API endpoints (`/health`, `/system/status`)
- [ ] Understand video file naming conventions
- [ ] Plan error handling strategy

### Video Selection
- [ ] Implement video listing with appropriate filters
- [ ] Add video validation before processing
- [ ] Handle pagination for large video collections
- [ ] Implement caching for video metadata

### Video Playback
- [ ] Test video streaming with range requests
- [ ] Implement thumbnail generation for previews
- [ ] Add progress tracking for video playback
- [ ] Handle different video formats (MP4, AVI)

### Error Handling
- [ ] Handle network connectivity issues
- [ ] Manage video not found scenarios
- [ ] Deal with invalid range requests
- [ ] Implement retry logic for transient failures

### Performance
- [ ] Use range requests for efficient seeking
- [ ] Implement client-side caching where appropriate
- [ ] Monitor bandwidth usage for video streaming
- [ ] Consider thumbnail caching for better UX

## 🎯 Next Steps

1. **Test Integration**: Use the provided examples to test basic connectivity
2. **Implement Error Handling**: Add robust error handling for production use
3. **Optimize Performance**: Implement caching and efficient streaming
4. **Monitor Usage**: Track API usage and performance metrics
5. **Security Review**: Consider authentication if exposing externally

This guide provides everything needed for successful integration with the USDA Vision Camera System's video streaming functionality. The system is designed to be simple and reliable for AI agents and external systems to consume video content efficiently.
