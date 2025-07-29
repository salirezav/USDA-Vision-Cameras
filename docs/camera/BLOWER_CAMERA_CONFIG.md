# Blower Camera (Camera1) Configuration

This document describes the default configuration for the blower camera (Camera1) based on the GigE camera settings from the dedicated software.

## Camera Identification
- **Camera Name**: camera1 (Blower-Yield-Cam)
- **Machine Topic**: blower_separator
- **Purpose**: Monitors the blower separator machine

## Configuration Summary

Based on the camera settings screenshots, the following configuration has been applied to Camera1:

### Exposure Settings
- **Mode**: Manual (not Auto)
- **Exposure Time**: 1.0ms (1000μs)
- **Gain**: 3.5x (350 in camera units)
- **Anti-Flicker**: Enabled (50Hz mode)

### Color Processing Settings
- **White Balance Mode**: Manual (not Auto)
- **Color Temperature**: D65 (6500K)
- **RGB Gain Values**:
  - Red Gain: 1.00
  - Green Gain: 1.00  
  - Blue Gain: 1.00
- **Saturation**: 100 (normal)

### LUT (Look-Up Table) Settings
- **Mode**: Dynamically generated (not Preset or Custom)
- **Gamma**: 1.00 (100 in config units)
- **Contrast**: 100 (normal)

### Advanced Settings
- **Anti-Flicker**: Enabled
- **Light Frequency**: 60Hz (1 in config)
- **Bit Depth**: 8-bit
- **HDR**: Disabled

## Configuration Mapping

The screenshots show these key settings that have been mapped to the config.json:

| Screenshot Setting | Config Parameter | Value | Notes |
|-------------------|------------------|-------|-------|
| Manual Exposure | auto_exposure | false | Exposure mode set to manual |
| Time(ms): 1.0000 | exposure_ms | 1.0 | Exposure time in milliseconds |
| Gain(multiple): 3.500 | gain | 3.5 | Analog gain multiplier |
| Manual White Balance | auto_white_balance | false | Manual WB mode |
| Color Temperature: D65 | color_temperature_preset | 6500 | D65 = 6500K |
| Red Gain: 1.00 | wb_red_gain | 1.0 | Manual RGB gain |
| Green Gain: 1.00 | wb_green_gain | 1.0 | Manual RGB gain |
| Blue Gain: 1.00 | wb_blue_gain | 1.0 | Manual RGB gain |
| Saturation: 100 | saturation | 100 | Color saturation |
| Gamma: 1.00 | gamma | 100 | Gamma correction |
| Contrast: 100 | contrast | 100 | Image contrast |
| 50HZ Anti-Flicker | anti_flicker_enabled | true | Flicker reduction |
| 60Hz frequency | light_frequency | 1 | Power frequency |

## Current Configuration

The current config.json for camera1 includes:

```json
{
  "name": "camera1",
  "machine_topic": "blower_separator",
  "storage_path": "/storage/camera1",
  "exposure_ms": 1.0,
  "gain": 3.5,
  "target_fps": 0,
  "enabled": true,
  "auto_start_recording_enabled": true,
  "auto_recording_max_retries": 3,
  "auto_recording_retry_delay_seconds": 2,
  "sharpness": 100,
  "contrast": 100,
  "saturation": 100,
  "gamma": 100,
  "noise_filter_enabled": false,
  "denoise_3d_enabled": false,
  "auto_white_balance": false,
  "color_temperature_preset": 6500,
  "anti_flicker_enabled": true,
  "light_frequency": 1,
  "bit_depth": 8,
  "hdr_enabled": false,
  "hdr_gain_mode": 0
}
```

## Camera Preview Enhancement

**Important Update**: The camera preview/streaming functionality has been enhanced to apply all default configuration settings from config.json, ensuring that preview images match the quality and appearance of recorded videos.

### What This Means for Camera1

When you view the camera preview, you'll now see:
- **Manual exposure** (1.0ms) and **high gain** (3.5x) applied
- **50Hz anti-flicker** filtering active
- **Manual white balance** with balanced RGB gains (1.0, 1.0, 1.0)
- **Standard image processing** (sharpness: 100, contrast: 100, gamma: 100, saturation: 100)
- **D65 color temperature** (6500K) applied

This ensures the preview accurately represents what will be recorded.

## Notes

1. **Machine Topic Correction**: The machine topic has been corrected from "vibratory_conveyor" to "blower_separator" to match the camera's actual monitoring purpose.

2. **Manual White Balance**: The camera is configured for manual white balance with D65 color temperature, which is appropriate for daylight conditions.

3. **RGB Gain Support**: The current configuration system needs to be extended to support individual RGB gain values for manual white balance fine-tuning.

4. **Anti-Flicker**: Enabled to reduce artificial lighting interference, set to 60Hz to match North American power frequency.

5. **LUT Mode**: The camera uses dynamically generated LUT with gamma=1.00 and contrast=100, which provides linear response.

## Future Enhancements

To fully support all settings shown in the screenshots, the following parameters should be added to the configuration system:

- `wb_red_gain`: Red channel gain for manual white balance (0.0-3.99)
- `wb_green_gain`: Green channel gain for manual white balance (0.0-3.99)  
- `wb_blue_gain`: Blue channel gain for manual white balance (0.0-3.99)
- `lut_mode`: LUT generation mode (0=dynamic, 1=preset, 2=custom)
- `lut_preset`: Preset LUT selection when using preset mode
