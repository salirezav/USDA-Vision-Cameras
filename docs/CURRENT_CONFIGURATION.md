# 📋 Current System Configuration Reference

## Overview
This document shows the exact current configuration structure of the USDA Vision Camera System, including all fields and their current values.

## 🔧 Complete Configuration Structure

### System Configuration (`config.json`)

```json
{
  "mqtt": {
    "broker_host": "192.168.1.110",
    "broker_port": 1883,
    "username": null,
    "password": null,
    "topics": {
      "vibratory_conveyor": "vision/vibratory_conveyor/state",
      "blower_separator": "vision/blower_separator/state"
    }
  },
  "storage": {
    "base_path": "/storage",
    "max_file_size_mb": 1000,
    "max_recording_duration_minutes": 60,
    "cleanup_older_than_days": 30
  },
  "system": {
    "camera_check_interval_seconds": 2,
    "log_level": "DEBUG",
    "log_file": "usda_vision_system.log",
    "api_host": "0.0.0.0",
    "api_port": 8000,
    "enable_api": true,
    "timezone": "America/New_York",
    "auto_recording_enabled": true
  },
  "cameras": [
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
      "sharpness": 0,
      "contrast": 100,
      "saturation": 100,
      "gamma": 100,
      "noise_filter_enabled": false,
      "denoise_3d_enabled": false,
      "auto_white_balance": false,
      "color_temperature_preset": 0,
      "wb_red_gain": 0.94,
      "wb_green_gain": 1.0,
      "wb_blue_gain": 0.87,
      "anti_flicker_enabled": false,
      "light_frequency": 0,
      "bit_depth": 8,
      "hdr_enabled": false,
      "hdr_gain_mode": 2
    },
    {
      "name": "camera2",
      "machine_topic": "vibratory_conveyor",
      "storage_path": "/storage/camera2",
      "exposure_ms": 0.2,
      "gain": 2.0,
      "target_fps": 0,
      "enabled": true,
      "video_format": "mp4",
      "video_codec": "mp4v",
      "video_quality": 95,
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
      "color_temperature_preset": 0,
      "wb_red_gain": 1.01,
      "wb_green_gain": 1.0,
      "wb_blue_gain": 0.87,
      "anti_flicker_enabled": false,
      "light_frequency": 0,
      "bit_depth": 8,
      "hdr_enabled": false,
      "hdr_gain_mode": 0
    }
  ]
}
```

## 📊 Configuration Field Reference

### MQTT Settings
| Field | Value | Description |
|-------|-------|-------------|
| `broker_host` | `"192.168.1.110"` | MQTT broker IP address |
| `broker_port` | `1883` | MQTT broker port |
| `username` | `null` | MQTT authentication (not used) |
| `password` | `null` | MQTT authentication (not used) |

### MQTT Topics
| Machine | Topic | Camera |
|---------|-------|--------|
| Vibratory Conveyor | `vision/vibratory_conveyor/state` | camera2 |
| Blower Separator | `vision/blower_separator/state` | camera1 |

### Storage Settings
| Field | Value | Description |
|-------|-------|-------------|
| `base_path` | `"/storage"` | Root storage directory |
| `max_file_size_mb` | `1000` | Maximum file size (1GB) |
| `max_recording_duration_minutes` | `60` | Maximum recording duration |
| `cleanup_older_than_days` | `30` | Auto-cleanup threshold |

### System Settings
| Field | Value | Description |
|-------|-------|-------------|
| `camera_check_interval_seconds` | `2` | Camera health check interval |
| `log_level` | `"DEBUG"` | Logging verbosity |
| `api_host` | `"0.0.0.0"` | API server bind address |
| `api_port` | `8000` | API server port |
| `timezone` | `"America/New_York"` | System timezone |
| `auto_recording_enabled` | `true` | Enable MQTT-triggered recording |

## 🎥 Camera Configuration Details

### Camera 1 (Blower Separator)
| Setting | Value | Description |
|---------|-------|-------------|
| **Basic Settings** | | |
| `name` | `"camera1"` | Camera identifier |
| `machine_topic` | `"blower_separator"` | MQTT topic to monitor |
| `storage_path` | `"/storage/camera1"` | Video storage location |
| `exposure_ms` | `0.3` | Exposure time (milliseconds) |
| `gain` | `4.0` | Camera gain multiplier |
| `target_fps` | `0` | Target FPS (0 = unlimited) |
| **Video Recording** | | |
| `video_format` | `"mp4"` | Video file format |
| `video_codec` | `"mp4v"` | Video codec (MPEG-4) |
| `video_quality` | `95` | Video quality (0-100) |
| **Auto Recording** | | |
| `auto_start_recording_enabled` | `true` | Enable auto-recording |
| `auto_recording_max_retries` | `3` | Max retry attempts |
| `auto_recording_retry_delay_seconds` | `2` | Delay between retries |
| **Image Quality** | | |
| `sharpness` | `0` | Sharpness adjustment |
| `contrast` | `100` | Contrast level |
| `saturation` | `100` | Color saturation |
| `gamma` | `100` | Gamma correction |
| **White Balance** | | |
| `auto_white_balance` | `false` | Auto white balance disabled |
| `wb_red_gain` | `0.94` | Red channel gain |
| `wb_green_gain` | `1.0` | Green channel gain |
| `wb_blue_gain` | `0.87` | Blue channel gain |
| **Advanced** | | |
| `bit_depth` | `8` | Color bit depth |
| `hdr_enabled` | `false` | HDR disabled |
| `hdr_gain_mode` | `2` | HDR gain mode |

### Camera 2 (Vibratory Conveyor)
| Setting | Value | Difference from Camera 1 |
|---------|-------|--------------------------|
| `name` | `"camera2"` | Different identifier |
| `machine_topic` | `"vibratory_conveyor"` | Different MQTT topic |
| `storage_path` | `"/storage/camera2"` | Different storage path |
| `exposure_ms` | `0.2` | Faster exposure (0.2 vs 0.3) |
| `gain` | `2.0` | Lower gain (2.0 vs 4.0) |
| `wb_red_gain` | `1.01` | Different red balance (1.01 vs 0.94) |
| `hdr_gain_mode` | `0` | Different HDR mode (0 vs 2) |

*All other settings are identical to Camera 1*

## 🔄 Recent Changes

### MP4 Format Update
- **Added**: `video_format`, `video_codec`, `video_quality` fields
- **Changed**: Default recording format from AVI to MP4
- **Impact**: Requires service restart to take effect

### Current Status
- ✅ Configuration updated with MP4 settings
- ⚠️ Service restart required to apply changes
- 📁 Existing AVI files remain accessible

## 📝 Notes

1. **Target FPS = 0**: Both cameras use unlimited frame rate for maximum capture speed
2. **Auto Recording**: Both cameras automatically start recording when their respective machines turn on
3. **White Balance**: Manual white balance settings optimized for each camera's environment
4. **Storage**: Each camera has its own dedicated storage directory
5. **Video Quality**: Set to 95/100 for high-quality recordings with MP4 compression benefits

## 🔧 Configuration Management

To modify these settings:
1. Edit `config.json` file
2. Restart the camera service: `sudo ./start_system.sh`
3. Verify changes via API: `GET /cameras/{camera_name}/config`

For real-time settings (exposure, gain, fps), use the API without restart:
```bash
PUT /cameras/{camera_name}/config
```
