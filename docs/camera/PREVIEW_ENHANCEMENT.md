# Camera Preview Enhancement

## Overview

The camera preview/streaming functionality has been significantly enhanced to apply all default configuration settings from `config.json`, ensuring that preview images accurately represent what will be recorded.

## Problem Solved

Previously, camera preview only applied basic settings (exposure, gain, trigger mode, frame rate), while recording applied the full configuration. This meant:

- Preview images looked different from recorded videos
- Color balance, sharpness, and other image quality settings were not visible in preview
- Users couldn't accurately assess the final recording quality from the preview

## Solution Implemented

The `CameraStreamer` class has been enhanced with comprehensive configuration methods that mirror those in `CameraRecorder`:

### New Configuration Methods Added

1. **`_configure_image_quality()`**
   - Applies sharpness settings (0-200)
   - Applies contrast settings (0-200) 
   - Applies gamma correction (0-300)
   - Applies saturation for color cameras (0-200)

2. **`_configure_color_settings()`**
   - Sets white balance mode (auto/manual)
   - Applies color temperature presets
   - Sets manual RGB gains for precise color tuning

3. **`_configure_advanced_settings()`**
   - Enables/disables anti-flicker filtering
   - Sets light frequency (50Hz/60Hz)
   - Configures HDR settings when available

4. **`_configure_noise_reduction()`**
   - Configures noise filter settings
   - Configures 3D denoising settings

### Enhanced Main Configuration Method

The `_configure_streaming_settings()` method now calls all configuration methods:

```python
def _configure_streaming_settings(self):
    """Configure camera settings from config.json for streaming"""
    try:
        # Basic settings (existing)
        mvsdk.CameraSetTriggerMode(self.hCamera, 0)
        mvsdk.CameraSetAeState(self.hCamera, 0)
        exposure_us = int(self.camera_config.exposure_ms * 1000)
        mvsdk.CameraSetExposureTime(self.hCamera, exposure_us)
        gain_value = int(self.camera_config.gain * 100)
        mvsdk.CameraSetAnalogGain(self.hCamera, gain_value)
        
        # Comprehensive configuration (new)
        self._configure_image_quality()
        self._configure_noise_reduction()
        if not self.monoCamera:
            self._configure_color_settings()
        self._configure_advanced_settings()
        
    except Exception as e:
        self.logger.warning(f"Could not configure some streaming settings: {e}")
```

## Benefits

### 1. WYSIWYG Preview
- **What You See Is What You Get**: Preview now accurately represents final recording quality
- **Real-time Assessment**: Users can evaluate recording quality before starting actual recording
- **Consistent Experience**: No surprises when comparing preview to recorded footage

### 2. Accurate Color Representation
- **Manual White Balance**: RGB gains are applied to preview for accurate color reproduction
- **Color Temperature**: D65 or other presets are applied consistently
- **Saturation**: Color intensity matches recording settings

### 3. Proper Image Quality
- **Sharpness**: Edge enhancement settings are visible in preview
- **Contrast**: Dynamic range adjustments are applied
- **Gamma**: Brightness curve corrections are active

### 4. Environmental Adaptation
- **Anti-Flicker**: Artificial lighting interference is filtered in preview
- **Light Frequency**: 50Hz/60Hz settings match local power grid
- **HDR**: High dynamic range processing when enabled

## Camera-Specific Impact

### Camera1 (Blower Separator)
Preview now shows:
- Manual exposure (1.0ms) and high gain (3.5x)
- 50Hz anti-flicker filtering
- Manual white balance with balanced RGB gains (1.0, 1.0, 1.0)
- Standard image processing (sharpness: 100, contrast: 100, gamma: 100, saturation: 100)
- D65 color temperature (6500K)

### Camera2 (Conveyor/Cracker)
Preview now shows:
- Manual exposure (0.5ms) and lower gain (0.3x)
- Custom RGB color tuning (R:1.01, G:1.00, B:0.87)
- No image sharpening (sharpness: 0)
- Enhanced saturation (100) and proper gamma (100)
- D65 color temperature with manual white balance

## Technical Implementation Details

### Error Handling
- All configuration methods include try-catch blocks
- Warnings are logged for unsupported features
- Graceful degradation when SDK functions are unavailable
- Streaming continues even if some settings fail to apply

### SDK Compatibility
- Checks for function availability before calling
- Handles different SDK versions gracefully
- Logs informational messages for unavailable features

### Performance Considerations
- Configuration is applied once during camera initialization
- No performance impact on streaming frame rate
- Separate camera instance for streaming (doesn't interfere with recording)

## Usage

No changes required for users - the enhancement is automatic:

1. **Start Preview**: Use existing preview endpoints
2. **View Stream**: Camera automatically applies all config.json settings
3. **Compare**: Preview now matches recording quality exactly

### API Endpoints (unchanged)
- `GET /cameras/{camera_name}/stream` - Get live MJPEG stream
- `POST /cameras/{camera_name}/start-stream` - Start streaming
- `POST /cameras/{camera_name}/stop-stream` - Stop streaming

## Future Enhancements

Additional settings that could be added to further improve preview accuracy:

1. **Geometric Corrections**
   - Lens distortion correction
   - Dead pixel correction
   - Flat fielding correction

2. **Image Transformations**
   - Rotation (90°, 180°, 270°)
   - Horizontal/vertical mirroring

3. **Advanced Processing**
   - Custom LUT (Look-Up Table) support
   - Advanced noise reduction algorithms
   - Real-time image enhancement filters

## Conclusion

This enhancement significantly improves the user experience by providing accurate, real-time preview of camera output with all configuration settings applied. Users can now confidently assess recording quality, adjust settings, and ensure optimal camera performance before starting critical recordings.
