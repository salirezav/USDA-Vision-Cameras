# Conveyor Camera (Camera2) Configuration

This document describes the default configuration for the conveyor camera (Camera2) based on the GigE camera settings from the dedicated software.

## Camera Identification
- **Camera Name**: camera2 (Cracker-Cam)
- **Machine Topic**: vibratory_conveyor
- **Purpose**: Monitors the vibratory conveyor/cracker machine

## Configuration Summary

Based on the camera settings screenshots, the following configuration has been applied to Camera2:

### Color Processing Settings
- **White Balance Mode**: Manual (not Auto)
- **Color Temperature**: D65 (6500K)
- **RGB Gain Values**:
  - Red Gain: 1.01
  - Green Gain: 1.00  
  - Blue Gain: 0.87
- **Saturation**: 100 (normal)

### LUT (Look-Up Table) Settings
- **Mode**: Dynamically generated (not Preset or Custom)
- **Gamma**: 1.00 (100 in config units)
- **Contrast**: 100 (normal)

### Graphic Processing Settings
- **Sharpness Level**: 0 (no sharpening applied)
- **Noise Reduction**: 
  - Denoise2D: Disabled
  - Denoise3D: Disabled
- **Rotation**: Disabled
- **Lens Distortion Correction**: Disabled
- **Dead Pixel Correction**: Enabled
- **Flat Fielding Correction**: Disabled

## Configuration Mapping

The screenshots show these key settings that have been mapped to the config.json:

| Screenshot Setting | Config Parameter | Value | Notes |
|-------------------|------------------|-------|-------|
| Manual White Balance | auto_white_balance | false | Manual WB mode |
| Color Temperature: D65 | color_temperature_preset | 6500 | D65 = 6500K |
| Red Gain: 1.01 | wb_red_gain | 1.01 | Manual RGB gain |
| Green Gain: 1.00 | wb_green_gain | 1.0 | Manual RGB gain |
| Blue Gain: 0.87 | wb_blue_gain | 0.87 | Manual RGB gain |
| Saturation: 100 | saturation | 100 | Color saturation |
| Gamma: 1.00 | gamma | 100 | Gamma correction |
| Contrast: 100 | contrast | 100 | Image contrast |
| Sharpen Level: 0 | sharpness | 0 | No sharpening |
| Denoise2D: Disabled | noise_filter_enabled | false | Basic noise filter off |
| Denoise3D: Disable | denoise_3d_enabled | false | Advanced denoising off |

## Current Configuration

The current config.json for camera2 includes:

```json
{
  "name": "camera2",
  "machine_topic": "vibratory_conveyor",
  "storage_path": "/storage/camera2",
  "exposure_ms": 0.5,
  "gain": 0.3,
  "target_fps": 0,
  "enabled": true,
  "auto_start_recording_enabled": true,
  "auto_recording_max_retries": 3,
  "auto_recording_retry_delay_seconds": 2,
  "sharpness": 0,
  "contrast": 100,
  "saturation": 100,
  "gamma": 100,
  "noise_filter_enabled": false,
  "denoise_3d_enabled": false,
  "auto_white_balance": false,
  "color_temperature_preset": 6500,
  "wb_red_gain": 1.01,
  "wb_green_gain": 1.0,
  "wb_blue_gain": 0.87,
  "anti_flicker_enabled": false,
  "light_frequency": 1,
  "bit_depth": 8,
  "hdr_enabled": false,
  "hdr_gain_mode": 0
}
```

## Key Differences from Camera1 (Blower Camera)

1. **RGB Gain Tuning**: Camera2 has custom RGB gains (R:1.01, G:1.00, B:0.87) vs Camera1's balanced gains (all 1.0)
2. **Sharpness**: Camera2 has sharpness disabled (0) vs Camera1's normal sharpness (100)
3. **Exposure/Gain**: Camera2 uses lower exposure (0.5ms) and gain (0.3x) vs Camera1's higher values (1.0ms, 3.5x)
4. **Anti-Flicker**: Camera2 has anti-flicker disabled vs Camera1's enabled anti-flicker

## Notes

1. **Custom White Balance**: Camera2 uses manual white balance with custom RGB gains, suggesting specific lighting conditions or color correction requirements for the conveyor monitoring.

2. **No Sharpening**: Sharpness is set to 0, indicating the raw image quality is preferred without artificial enhancement.

3. **Minimal Noise Reduction**: Both 2D and 3D denoising are disabled, prioritizing image authenticity over noise reduction.

4. **Dead Pixel Correction**: Enabled to handle any defective pixels on the sensor.

5. **Lower Sensitivity**: The lower exposure and gain settings suggest better lighting conditions or different monitoring requirements compared to the blower camera.

## Camera Preview Enhancement

**Important Update**: The camera preview/streaming functionality has been enhanced to apply all default configuration settings from config.json, ensuring that preview images match the quality and appearance of recorded videos.

### What Changed

Previously, camera preview only applied basic settings (exposure, gain, trigger mode). Now, the preview applies the complete configuration including:

- **Image Quality**: Sharpness, contrast, gamma, saturation
- **Color Processing**: White balance mode, color temperature, RGB gains
- **Advanced Settings**: Anti-flicker, light frequency, HDR settings
- **Noise Reduction**: Filter and 3D denoising settings (where supported)

### Benefits

1. **WYSIWYG Preview**: What you see in the preview is exactly what gets recorded
2. **Accurate Color Representation**: Manual white balance and RGB gains are applied to preview
3. **Consistent Image Quality**: Sharpness, contrast, and gamma settings match recording
4. **Proper Exposure**: Anti-flicker and lighting frequency settings are applied

### Technical Implementation

The `CameraStreamer` class now includes the same comprehensive configuration methods as `CameraRecorder`:

- `_configure_image_quality()`: Applies sharpness, contrast, gamma, saturation
- `_configure_color_settings()`: Applies white balance mode, color temperature, RGB gains
- `_configure_advanced_settings()`: Applies anti-flicker, light frequency, HDR
- `_configure_noise_reduction()`: Applies noise filter settings

These methods are called during camera initialization for streaming, ensuring all config.json settings are applied.

## Future Enhancements

Additional parameters that could be added to support all graphic processing features:

- `rotation_angle`: Image rotation (0, 90, 180, 270 degrees)
- `lens_distortion_correction`: Enable/disable lens distortion correction
- `dead_pixel_correction`: Enable/disable dead pixel correction
- `flat_fielding_correction`: Enable/disable flat fielding correction
- `mirror_horizontal`: Horizontal mirroring
- `mirror_vertical`: Vertical mirroring
