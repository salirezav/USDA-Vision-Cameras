# API Changes Summary: Camera Settings and Video Format Updates

## Overview
This document tracks major API changes including camera settings enhancements and the MP4 video format update.

## 🎥 Latest Update: MP4 Video Format (v2.1)
**Date**: August 2025

**Major Changes**:
- **Video Format**: Changed from AVI/XVID to MP4/MPEG-4 format
- **File Extensions**: New recordings use `.mp4` instead of `.avi`
- **File Size**: ~40% reduction in file sizes
- **Streaming**: Better web browser compatibility

**New Configuration Fields**:
```json
{
  "video_format": "mp4",      // File format: "mp4" or "avi"
  "video_codec": "mp4v",      // Video codec: "mp4v", "XVID", "MJPG"
  "video_quality": 95         // Quality: 0-100 (higher = better)
}
```

**Frontend Impact**:
- ✅ Better streaming performance and browser support
- ✅ Smaller file sizes for faster transfers
- ✅ Universal HTML5 video player compatibility
- ✅ Backward compatible with existing AVI files

**Documentation**: See [MP4 Format Update Guide](MP4_FORMAT_UPDATE.md)

---

## Previous Changes: Camera Settings and Filename Handling

Enhanced the `POST /cameras/{camera_name}/start-recording` API endpoint to accept optional camera settings (shutter speed/exposure, gain, and fps) and ensure all filenames have datetime prefixes.

## Changes Made

### 1. API Models (`usda_vision_system/api/models.py`)
- **Enhanced `StartRecordingRequest`** to include optional parameters:
  - `exposure_ms: Optional[float]` - Exposure time in milliseconds
  - `gain: Optional[float]` - Camera gain value  
  - `fps: Optional[float]` - Target frames per second

### 2. Camera Recorder (`usda_vision_system/camera/recorder.py`)
- **Added `update_camera_settings()` method** to dynamically update camera settings:
  - Updates exposure time using `mvsdk.CameraSetExposureTime()`
  - Updates gain using `mvsdk.CameraSetAnalogGain()`
  - Updates target FPS in camera configuration
  - Logs all setting changes
  - Returns boolean indicating success/failure

### 3. Camera Manager (`usda_vision_system/camera/manager.py`)
- **Enhanced `manual_start_recording()` method** to accept new parameters:
  - Added optional `exposure_ms`, `gain`, and `fps` parameters
  - Calls `update_camera_settings()` if any settings are provided
  - **Automatic datetime prefix**: Always prepends timestamp to filename
  - If custom filename provided: `{timestamp}_{custom_filename}`
  - If no filename provided: `{camera_name}_manual_{timestamp}.avi`

### 4. API Server (`usda_vision_system/api/server.py`)
- **Updated start-recording endpoint** to:
  - Pass new camera settings to camera manager
  - Handle filename response with datetime prefix
  - Maintain backward compatibility with existing requests

### 5. API Tests (`api-tests.http`)
- **Added comprehensive test examples**:
  - Basic recording (existing functionality)
  - Recording with camera settings
  - Recording with settings only (no filename)
  - Different parameter combinations

## Usage Examples

### Basic Recording (unchanged)
```http
POST http://localhost:8000/cameras/camera1/start-recording
Content-Type: application/json

{
  "camera_name": "camera1",
  "filename": "test.avi"
}
```
**Result**: File saved as `20241223_143022_test.avi`

### Recording with Camera Settings
```http
POST http://localhost:8000/cameras/camera1/start-recording
Content-Type: application/json

{
  "camera_name": "camera1",
  "filename": "high_quality.avi",
  "exposure_ms": 2.0,
  "gain": 4.0,
  "fps": 5.0
}
```
**Result**:
- Camera settings updated before recording
- File saved as `20241223_143022_high_quality.avi`

### Maximum FPS Recording
```http
POST http://localhost:8000/cameras/camera1/start-recording
Content-Type: application/json

{
  "camera_name": "camera1",
  "filename": "max_speed.avi",
  "exposure_ms": 0.1,
  "gain": 1.0,
  "fps": 0
}
```
**Result**:
- Camera captures at maximum possible speed (no delay between frames)
- Video file saved with 30 FPS metadata for proper playback
- Actual capture rate depends on camera hardware and exposure settings

### Settings Only (no filename)
```http
POST http://localhost:8000/cameras/camera1/start-recording
Content-Type: application/json

{
  "camera_name": "camera1",
  "exposure_ms": 1.5,
  "gain": 3.0,
  "fps": 7.0
}
```
**Result**: 
- Camera settings updated
- File saved as `camera1_manual_20241223_143022.avi`

## Key Features

### 1. **Backward Compatibility**
- All existing API calls continue to work unchanged
- New parameters are optional
- Default behavior preserved when no settings provided

### 2. **Automatic Datetime Prefix**
- **ALL filenames now have datetime prefix** regardless of what's sent
- Format: `YYYYMMDD_HHMMSS_` (Atlanta timezone)
- Ensures unique filenames and chronological ordering

### 3. **Dynamic Camera Settings**
- Settings can be changed per recording without restarting system
- Based on proven implementation from `old tests/camera_video_recorder.py`
- Proper error handling and logging

### 4. **Maximum FPS Capture**
- **`fps: 0`** = Capture at maximum possible speed (no delay between frames)
- **`fps > 0`** = Capture at specified frame rate with controlled timing
- **`fps` omitted** = Uses camera config default (usually 3.0 fps)
- Video files saved with 30 FPS metadata when fps=0 for proper playback

### 5. **Parameter Validation**
- Uses Pydantic models for automatic validation
- Optional parameters with proper type checking
- Descriptive field documentation

## Testing

Run the test script to verify functionality:
```bash
# Start the system first
python main.py

# In another terminal, run tests
python test_api_changes.py
```

The test script verifies:
- Basic recording functionality
- Camera settings application
- Filename datetime prefix handling
- API response accuracy

## Implementation Notes

### Camera Settings Mapping
- **Exposure**: Converted from milliseconds to microseconds for SDK
- **Gain**: Converted to camera units (multiplied by 100)
- **FPS**: Stored in camera config, used by recording loop

### Error Handling
- Settings update failures are logged but don't prevent recording
- Invalid camera names return appropriate HTTP errors
- Camera initialization failures are handled gracefully

### Filename Generation
- Uses `format_filename_timestamp()` from timezone utilities
- Ensures Atlanta timezone consistency
- Handles both custom and auto-generated filenames

## Similar to Old Implementation
The camera settings functionality mirrors the proven approach in `old tests/camera_video_recorder.py`:
- Same parameter names and ranges
- Same SDK function calls
- Same conversion factors
- Proven to work with the camera hardware
