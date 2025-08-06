# 🎥 MP4 Video Format Update - Frontend Integration Guide

## Overview
The USDA Vision Camera System has been updated to record videos in **MP4 format** instead of AVI format for better streaming compatibility and smaller file sizes.

## 🔄 What Changed

### Video Format
- **Before**: AVI files with XVID codec (`.avi` extension)
- **After**: MP4 files with MPEG-4 codec (`.mp4` extension)

### File Extensions
- All new video recordings now use `.mp4` extension
- Existing `.avi` files remain accessible and functional
- File size reduction: ~40% smaller than equivalent AVI files

### API Response Updates
New fields added to camera configuration responses:

```json
{
  "video_format": "mp4",      // File format: "mp4" or "avi"
  "video_codec": "mp4v",      // Video codec: "mp4v", "XVID", "MJPG"
  "video_quality": 95         // Quality: 0-100 (higher = better)
}
```

## 🌐 Frontend Impact

### 1. Video Player Compatibility
**✅ Better Browser Support**
- MP4 format has native support in all modern browsers
- No need for additional codecs or plugins
- Better mobile device compatibility (iOS/Android)

### 2. File Handling Updates
**File Extension Handling**
```javascript
// Update file extension checks
const isVideoFile = (filename) => {
  return filename.endsWith('.mp4') || filename.endsWith('.avi');
};

// Video MIME type detection
const getVideoMimeType = (filename) => {
  if (filename.endsWith('.mp4')) return 'video/mp4';
  if (filename.endsWith('.avi')) return 'video/x-msvideo';
  return 'video/mp4'; // default
};
```

### 3. Video Streaming
**Improved Streaming Performance**
```javascript
// MP4 files can be streamed directly without conversion
const videoUrl = `/api/videos/${videoId}/stream`;

// For HTML5 video element
<video controls>
  <source src={videoUrl} type="video/mp4" />
  Your browser does not support the video tag.
</video>
```

### 4. File Size Display
**Updated Size Expectations**
- MP4 files are ~40% smaller than equivalent AVI files
- Update any file size warnings or storage calculations
- Better compression means faster downloads and uploads

## 📡 API Changes

### Camera Configuration Endpoint
**GET** `/cameras/{camera_name}/config`

**New Response Fields:**
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

### Video Listing Endpoints
**File Extension Updates**
- Video files in responses will now have `.mp4` extensions
- Existing `.avi` files will still appear in listings
- Filter by both extensions when needed

## 🔧 Configuration Options

### Video Format Settings
```json
{
  "video_format": "mp4",     // Options: "mp4", "avi"
  "video_codec": "mp4v",     // Options: "mp4v", "XVID", "MJPG"
  "video_quality": 95        // Range: 0-100 (higher = better quality)
}
```

### Recommended Settings
- **Production**: `"mp4"` format, `"mp4v"` codec, `95` quality
- **Storage Optimized**: `"mp4"` format, `"mp4v"` codec, `85` quality
- **Legacy Mode**: `"avi"` format, `"XVID"` codec, `95` quality

## 🎯 Frontend Implementation Checklist

### ✅ Video Player Updates
- [ ] Verify HTML5 video player works with MP4 files
- [ ] Update video MIME type handling
- [ ] Test streaming performance with new format

### ✅ File Management
- [ ] Update file extension filters to include `.mp4`
- [ ] Modify file type detection logic
- [ ] Update download/upload handling for MP4 files

### ✅ UI/UX Updates
- [ ] Update file size expectations in UI
- [ ] Modify any format-specific icons or indicators
- [ ] Update help text or tooltips mentioning video formats

### ✅ Configuration Interface
- [ ] Add video format settings to camera config UI
- [ ] Include video quality slider/selector
- [ ] Add restart warning for video format changes

### ✅ Testing
- [ ] Test video playback with new MP4 files
- [ ] Verify backward compatibility with existing AVI files
- [ ] Test streaming performance and loading times

## 🔄 Backward Compatibility

### Existing AVI Files
- All existing `.avi` files remain fully functional
- No conversion or migration required
- Video player should handle both formats

### API Compatibility
- All existing API endpoints continue to work
- New fields are additive (won't break existing code)
- Default values provided for new configuration fields

## 📊 Performance Benefits

### File Size Reduction
```
Example 5-minute recording at 1280x1024:
- AVI/XVID: ~180 MB
- MP4/MPEG-4: ~108 MB (40% reduction)
```

### Streaming Improvements
- Faster initial load times
- Better progressive download support
- Reduced bandwidth usage
- Native browser optimization

### Storage Efficiency
- More recordings fit in same storage space
- Faster backup and transfer operations
- Reduced storage costs over time

## 🚨 Important Notes

### Restart Required
- Video format changes require camera service restart
- Mark video format settings as "restart required" in UI
- Provide clear user feedback about restart necessity

### Browser Compatibility
- MP4 format supported in all modern browsers
- Better mobile device support than AVI
- No additional plugins or codecs needed

### Quality Assurance
- Video quality maintained at 95/100 setting
- No visual degradation compared to AVI
- High bitrate ensures professional quality

## 🔗 Related Documentation

- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [Camera Configuration API](api/CAMERA_CONFIG_API.md) - Detailed config options
- [Video Streaming Guide](VIDEO_STREAMING.md) - Streaming implementation
- [MP4 Conversion Summary](../MP4_CONVERSION_SUMMARY.md) - Technical details

## 📞 Support

If you encounter any issues with the MP4 format update:

1. **Video Playback Issues**: Check browser console for codec errors
2. **File Size Concerns**: Verify quality settings in camera config
3. **Streaming Problems**: Test with both MP4 and AVI files for comparison
4. **API Integration**: Refer to updated API documentation

The MP4 format provides better web compatibility and performance while maintaining the same high video quality required for the USDA vision system.
