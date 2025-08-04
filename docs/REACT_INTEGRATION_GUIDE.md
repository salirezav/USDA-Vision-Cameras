# 🚀 React Frontend Integration Guide - MP4 Update

## 🎯 Quick Summary for React Team

The camera system now records in **MP4 format** instead of AVI. This provides better web compatibility and smaller file sizes.

## 🔄 What You Need to Update

### 1. File Extension Handling
```javascript
// OLD: Only checked for .avi
const isVideoFile = (filename) => filename.endsWith('.avi');

// NEW: Check for both formats
const isVideoFile = (filename) => {
  return filename.endsWith('.mp4') || filename.endsWith('.avi');
};

// Video MIME types
const getVideoMimeType = (filename) => {
  if (filename.endsWith('.mp4')) return 'video/mp4';
  if (filename.endsWith('.avi')) return 'video/x-msvideo';
  return 'video/mp4'; // default for new files
};
```

### 2. Video Player Component
```jsx
// MP4 files work better with HTML5 video
const VideoPlayer = ({ videoUrl, filename }) => {
  const mimeType = getVideoMimeType(filename);
  
  return (
    <video controls width="100%" height="auto">
      <source src={videoUrl} type={mimeType} />
      Your browser does not support the video tag.
    </video>
  );
};
```

### 3. Camera Configuration Interface
Add these new fields to your camera config forms:

```jsx
const CameraConfigForm = () => {
  const [config, setConfig] = useState({
    // ... existing fields
    video_format: 'mp4',    // 'mp4' or 'avi'
    video_codec: 'mp4v',    // 'mp4v', 'XVID', 'MJPG'
    video_quality: 95       // 0-100
  });

  return (
    <form>
      {/* ... existing fields */}
      
      <div className="video-settings">
        <h3>Video Recording Settings</h3>
        
        <select 
          value={config.video_format}
          onChange={(e) => setConfig({...config, video_format: e.target.value})}
        >
          <option value="mp4">MP4 (Recommended)</option>
          <option value="avi">AVI (Legacy)</option>
        </select>
        
        <select 
          value={config.video_codec}
          onChange={(e) => setConfig({...config, video_codec: e.target.value})}
        >
          <option value="mp4v">MPEG-4 (mp4v)</option>
          <option value="XVID">Xvid</option>
          <option value="MJPG">Motion JPEG</option>
        </select>
        
        <input 
          type="range" 
          min="50" 
          max="100" 
          value={config.video_quality}
          onChange={(e) => setConfig({...config, video_quality: parseInt(e.target.value)})}
        />
        <label>Quality: {config.video_quality}%</label>
        
        <div className="warning">
          ⚠️ Video format changes require camera restart
        </div>
      </div>
    </form>
  );
};
```

## 📡 API Response Changes

### Camera Configuration Response
```json
{
  "name": "camera1",
  "machine_topic": "blower_separator",
  "storage_path": "/storage/camera1",
  "exposure_ms": 0.3,
  "gain": 4.0,
  "target_fps": 0,
  "enabled": true,
  "video_format": "mp4",
  "video_codec": "mp4v",
  "video_quality": 95,
  "auto_start_recording_enabled": true,
  "auto_recording_max_retries": 3,
  "auto_recording_retry_delay_seconds": 2,

  // ... other existing fields
}
```

### Video File Listings
```json
{
  "videos": [
    {
      "file_id": "camera1_recording_20250804_143022.mp4",
      "filename": "camera1_recording_20250804_143022.mp4",
      "format": "mp4",
      "file_size_bytes": 31457280,
      "created_at": "2025-08-04T14:30:22"
    }
  ]
}
```

## 🎨 UI/UX Improvements

### File Size Display
```javascript
// MP4 files are ~40% smaller
const formatFileSize = (bytes) => {
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(1)} MB`;
};

// Show format in file listings
const FileListItem = ({ video }) => (
  <div className="file-item">
    <span className="filename">{video.filename}</span>
    <span className={`format ${video.format}`}>
      {video.format.toUpperCase()}
    </span>
    <span className="size">{formatFileSize(video.file_size_bytes)}</span>
  </div>
);
```

### Format Indicators
```css
.format.mp4 {
  background: #4CAF50;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.8em;
}

.format.avi {
  background: #FF9800;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.8em;
}
```

## ⚡ Performance Benefits

### Streaming Improvements
- **Faster Loading**: MP4 files start playing sooner
- **Better Seeking**: More responsive video scrubbing
- **Mobile Friendly**: Better iOS/Android compatibility
- **Bandwidth Savings**: 40% smaller files = faster transfers

### Implementation Tips
```javascript
// Preload video metadata for better UX
const VideoThumbnail = ({ videoUrl }) => (
  <video 
    preload="metadata"
    poster={`${videoUrl}?t=1`} // Thumbnail at 1 second
    onLoadedMetadata={(e) => {
      console.log('Duration:', e.target.duration);
    }}
  >
    <source src={videoUrl} type="video/mp4" />
  </video>
);
```

## 🔧 Configuration Management

### Restart Warning Component
```jsx
const RestartWarning = ({ show }) => {
  if (!show) return null;
  
  return (
    <div className="alert alert-warning">
      <strong>⚠️ Restart Required</strong>
      <p>Video format changes require a camera service restart to take effect.</p>
      <button onClick={handleRestart}>Restart Camera Service</button>
    </div>
  );
};
```

### Settings Validation
```javascript
const validateVideoSettings = (settings) => {
  const errors = {};
  
  if (!['mp4', 'avi'].includes(settings.video_format)) {
    errors.video_format = 'Must be mp4 or avi';
  }
  
  if (!['mp4v', 'XVID', 'MJPG'].includes(settings.video_codec)) {
    errors.video_codec = 'Invalid codec';
  }
  
  if (settings.video_quality < 50 || settings.video_quality > 100) {
    errors.video_quality = 'Quality must be between 50-100';
  }
  
  return errors;
};
```

## 📱 Mobile Considerations

### Responsive Video Player
```jsx
const ResponsiveVideoPlayer = ({ videoUrl, filename }) => (
  <div className="video-container">
    <video 
      controls 
      playsInline // Important for iOS
      preload="metadata"
      style={{ width: '100%', height: 'auto' }}
    >
      <source src={videoUrl} type={getVideoMimeType(filename)} />
      <p>Your browser doesn't support HTML5 video.</p>
    </video>
  </div>
);
```

## 🧪 Testing Checklist

- [ ] Video playback works with new MP4 files
- [ ] File extension filtering includes both .mp4 and .avi
- [ ] Camera configuration UI shows video format options
- [ ] Restart warning appears for video format changes
- [ ] File size displays are updated for smaller MP4 files
- [ ] Mobile video playback works correctly
- [ ] Video streaming performance is improved
- [ ] Backward compatibility with existing AVI files

## 📞 Support

If you encounter issues:

1. **Video won't play**: Check browser console for codec errors
2. **File size unexpected**: Verify quality settings in camera config
3. **Streaming slow**: Compare MP4 vs AVI performance
4. **Mobile issues**: Ensure `playsInline` attribute is set

The MP4 update provides significant improvements in web compatibility and performance while maintaining full backward compatibility with existing AVI files.
