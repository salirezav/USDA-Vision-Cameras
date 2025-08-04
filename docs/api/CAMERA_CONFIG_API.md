# 🎛️ Camera Configuration API Guide

This guide explains how to configure camera settings via API endpoints, including all the advanced settings from your config.json.

> **Note**: This document is part of the comprehensive [USDA Vision Camera System API Documentation](../API_DOCUMENTATION.md). For complete API reference, see the main documentation.

## 📋 Configuration Categories

### ✅ **Real-time Configurable (No Restart Required)**
These settings can be changed while the camera is active:

- **Basic**: `exposure_ms`, `gain`, `target_fps`
- **Image Quality**: `sharpness`, `contrast`, `saturation`, `gamma`
- **Color**: `auto_white_balance`, `color_temperature_preset`
- **White Balance**: `wb_red_gain`, `wb_green_gain`, `wb_blue_gain`
- **Advanced**: `anti_flicker_enabled`, `light_frequency`
- **HDR**: `hdr_enabled`, `hdr_gain_mode`

### ⚠️ **Restart Required**
These settings require camera restart to take effect:

- **Noise Reduction**: `noise_filter_enabled`, `denoise_3d_enabled`
- **Video Recording**: `video_format`, `video_codec`, `video_quality`
- **System**: `machine_topic`, `storage_path`, `enabled`, `bit_depth`

### 🔒 **Read-Only Fields**
These fields are returned in the response but cannot be modified via the API:

- **System Info**: `name`, `machine_topic`, `storage_path`, `enabled`
- **Auto-Recording**: `auto_start_recording_enabled`, `auto_recording_max_retries`, `auto_recording_retry_delay_seconds`

## 🔌 API Endpoints

### 1. Get Camera Configuration
```http
GET /cameras/{camera_name}/config
```

**Response:**
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
}
```

### 2. Update Camera Configuration
```http
PUT /cameras/{camera_name}/config
Content-Type: application/json
```

**Request Body (all fields optional):**
```json
{
  "exposure_ms": 2.0,
  "gain": 4.0,
  "target_fps": 10.0,
  "sharpness": 150,
  "contrast": 120,
  "saturation": 110,
  "gamma": 90,
  "noise_filter_enabled": true,
  "denoise_3d_enabled": false,
  "auto_white_balance": false,
  "color_temperature_preset": 1,
  "wb_red_gain": 1.2,
  "wb_green_gain": 1.0,
  "wb_blue_gain": 0.8,
  "anti_flicker_enabled": true,
  "light_frequency": 1,
  "hdr_enabled": false,
  "hdr_gain_mode": 0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Camera camera1 configuration updated",
  "updated_settings": ["exposure_ms", "gain", "sharpness", "wb_red_gain"]
}
```

### 3. Apply Configuration (Restart Camera)
```http
POST /cameras/{camera_name}/apply-config
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration applied to camera camera1"
}
```

## 📊 Setting Ranges and Descriptions

### System Settings
| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `name` | string | - | Camera identifier (read-only) |
| `machine_topic` | string | - | MQTT topic for machine state (read-only) |
| `storage_path` | string | - | Video storage directory (read-only) |
| `enabled` | true/false | true | Camera enabled status (read-only) |

### Auto-Recording Settings
| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| `auto_start_recording_enabled` | true/false | true | Enable automatic recording on machine state changes (read-only) |
| `auto_recording_max_retries` | 1-10 | 3 | Maximum retry attempts for failed recordings (read-only) |
| `auto_recording_retry_delay_seconds` | 1-30 | 2 | Delay between retry attempts in seconds (read-only) |

### Basic Settings
| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| `exposure_ms` | 0.1 - 1000.0 | 1.0 | Exposure time in milliseconds |
| `gain` | 0.0 - 20.0 | 3.5 | Camera gain multiplier |
| `target_fps` | 0.0 - 120.0 | 0 | Target FPS (0 = maximum) |

### Image Quality Settings
| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| `sharpness` | 0 - 200 | 100 | Image sharpness (100 = no sharpening) |
| `contrast` | 0 - 200 | 100 | Image contrast (100 = normal) |
| `saturation` | 0 - 200 | 100 | Color saturation (color cameras only) |
| `gamma` | 0 - 300 | 100 | Gamma correction (100 = normal) |

### Color Settings
| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `auto_white_balance` | true/false | true | Automatic white balance |
| `color_temperature_preset` | 0-10 | 0 | Color temperature preset (0=auto) |

### Manual White Balance RGB Gains
| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| `wb_red_gain` | 0.0 - 3.99 | 1.0 | Red channel gain for manual white balance |
| `wb_green_gain` | 0.0 - 3.99 | 1.0 | Green channel gain for manual white balance |
| `wb_blue_gain` | 0.0 - 3.99 | 1.0 | Blue channel gain for manual white balance |

### Advanced Settings
| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `anti_flicker_enabled` | true/false | true | Reduce artificial lighting flicker |
| `light_frequency` | 0/1 | 1 | Light frequency (0=50Hz, 1=60Hz) |
| `noise_filter_enabled` | true/false | true | Basic noise filtering |
| `denoise_3d_enabled` | true/false | false | Advanced 3D denoising |

### HDR Settings
| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `hdr_enabled` | true/false | false | High Dynamic Range |
| `hdr_gain_mode` | 0-3 | 0 | HDR processing mode |

## 🚀 Usage Examples

### Example 1: Adjust Exposure and Gain
```bash
curl -X PUT http://localhost:8000/cameras/camera1/config \
  -H "Content-Type: application/json" \
  -d '{
    "exposure_ms": 1.5,
    "gain": 4.0
  }'
```

### Example 2: Improve Image Quality
```bash
curl -X PUT http://localhost:8000/cameras/camera1/config \
  -H "Content-Type: application/json" \
  -d '{
    "sharpness": 150,
    "contrast": 120,
    "gamma": 90
  }'
```

### Example 3: Configure for Indoor Lighting
```bash
curl -X PUT http://localhost:8000/cameras/camera1/config \
  -H "Content-Type: application/json" \
  -d '{
    "anti_flicker_enabled": true,
    "light_frequency": 1,
    "auto_white_balance": false,
    "color_temperature_preset": 2
  }'
```

### Example 4: Enable HDR Mode
```bash
curl -X PUT http://localhost:8000/cameras/camera1/config \
  -H "Content-Type: application/json" \
  -d '{
    "hdr_enabled": true,
    "hdr_gain_mode": 1
  }'
```

## ⚛️ React Integration Examples

### Camera Configuration Component
```jsx
import React, { useState, useEffect } from 'react';

const CameraConfig = ({ cameraName, apiBaseUrl = 'http://localhost:8000' }) => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load current configuration
  useEffect(() => {
    fetchConfig();
  }, [cameraName]);

  const fetchConfig = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/cameras/${cameraName}/config`);
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      } else {
        setError('Failed to load configuration');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    }
  };

  const updateConfig = async (updates) => {
    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/cameras/${cameraName}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Updated settings:', result.updated_settings);
        await fetchConfig(); // Reload configuration
      } else {
        const error = await response.json();
        setError(error.detail || 'Update failed');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSliderChange = (setting, value) => {
    updateConfig({ [setting]: value });
  };

  if (!config) return <div>Loading configuration...</div>;

  return (
    <div className="camera-config">
      <h3>Camera Configuration: {cameraName}</h3>

      {/* System Information (Read-Only) */}
      <div className="config-section">
        <h4>System Information</h4>
        <div className="info-grid">
          <div><strong>Name:</strong> {config.name}</div>
          <div><strong>Machine Topic:</strong> {config.machine_topic}</div>
          <div><strong>Storage Path:</strong> {config.storage_path}</div>
          <div><strong>Enabled:</strong> {config.enabled ? 'Yes' : 'No'}</div>
          <div><strong>Auto Recording:</strong> {config.auto_start_recording_enabled ? 'Enabled' : 'Disabled'}</div>
          <div><strong>Max Retries:</strong> {config.auto_recording_max_retries}</div>
          <div><strong>Retry Delay:</strong> {config.auto_recording_retry_delay_seconds}s</div>
        </div>
      </div>

      {/* Basic Settings */}
      <div className="config-section">
        <h4>Basic Settings</h4>
        
        <div className="setting">
          <label>Exposure (ms): {config.exposure_ms}</label>
          <input
            type="range"
            min="0.1"
            max="10"
            step="0.1"
            value={config.exposure_ms}
            onChange={(e) => handleSliderChange('exposure_ms', parseFloat(e.target.value))}
          />
        </div>

        <div className="setting">
          <label>Gain: {config.gain}</label>
          <input
            type="range"
            min="0"
            max="10"
            step="0.1"
            value={config.gain}
            onChange={(e) => handleSliderChange('gain', parseFloat(e.target.value))}
          />
        </div>

        <div className="setting">
          <label>Target FPS: {config.target_fps}</label>
          <input
            type="range"
            min="0"
            max="30"
            step="1"
            value={config.target_fps}
            onChange={(e) => handleSliderChange('target_fps', parseInt(e.target.value))}
          />
        </div>
      </div>

      {/* Image Quality Settings */}
      <div className="config-section">
        <h4>Image Quality</h4>
        
        <div className="setting">
          <label>Sharpness: {config.sharpness}</label>
          <input
            type="range"
            min="0"
            max="200"
            value={config.sharpness}
            onChange={(e) => handleSliderChange('sharpness', parseInt(e.target.value))}
          />
        </div>

        <div className="setting">
          <label>Contrast: {config.contrast}</label>
          <input
            type="range"
            min="0"
            max="200"
            value={config.contrast}
            onChange={(e) => handleSliderChange('contrast', parseInt(e.target.value))}
          />
        </div>

        <div className="setting">
          <label>Gamma: {config.gamma}</label>
          <input
            type="range"
            min="0"
            max="300"
            value={config.gamma}
            onChange={(e) => handleSliderChange('gamma', parseInt(e.target.value))}
          />
        </div>
      </div>

      {/* White Balance RGB Gains */}
      <div className="config-section">
        <h4>White Balance RGB Gains</h4>

        <div className="setting">
          <label>Red Gain: {config.wb_red_gain}</label>
          <input
            type="range"
            min="0"
            max="3.99"
            step="0.01"
            value={config.wb_red_gain}
            onChange={(e) => handleSliderChange('wb_red_gain', parseFloat(e.target.value))}
          />
        </div>

        <div className="setting">
          <label>Green Gain: {config.wb_green_gain}</label>
          <input
            type="range"
            min="0"
            max="3.99"
            step="0.01"
            value={config.wb_green_gain}
            onChange={(e) => handleSliderChange('wb_green_gain', parseFloat(e.target.value))}
          />
        </div>

        <div className="setting">
          <label>Blue Gain: {config.wb_blue_gain}</label>
          <input
            type="range"
            min="0"
            max="3.99"
            step="0.01"
            value={config.wb_blue_gain}
            onChange={(e) => handleSliderChange('wb_blue_gain', parseFloat(e.target.value))}
          />
        </div>
      </div>

      {/* Advanced Settings */}
      <div className="config-section">
        <h4>Advanced Settings</h4>
        
        <div className="setting">
          <label>
            <input
              type="checkbox"
              checked={config.anti_flicker_enabled}
              onChange={(e) => updateConfig({ anti_flicker_enabled: e.target.checked })}
            />
            Anti-flicker Enabled
          </label>
        </div>

        <div className="setting">
          <label>
            <input
              type="checkbox"
              checked={config.auto_white_balance}
              onChange={(e) => updateConfig({ auto_white_balance: e.target.checked })}
            />
            Auto White Balance
          </label>
        </div>

        <div className="setting">
          <label>
            <input
              type="checkbox"
              checked={config.hdr_enabled}
              onChange={(e) => updateConfig({ hdr_enabled: e.target.checked })}
            />
            HDR Enabled
          </label>
        </div>
      </div>

      {error && (
        <div className="error" style={{ color: 'red', marginTop: '10px' }}>
          {error}
        </div>
      )}

      {loading && <div>Updating configuration...</div>}
    </div>
  );
};

export default CameraConfig;
```

## 🔄 Configuration Workflow

### 1. Real-time Adjustments
For settings that don't require restart:
```bash
# Update settings
curl -X PUT /cameras/camera1/config -d '{"exposure_ms": 2.0}'

# Settings take effect immediately
# Continue recording/streaming without interruption
```

### 2. Settings Requiring Restart
For noise reduction and system settings:
```bash
# Update settings
curl -X PUT /cameras/camera1/config -d '{"noise_filter_enabled": false}'

# Apply configuration (restarts camera)
curl -X POST /cameras/camera1/apply-config

# Camera reinitializes with new settings
```

## 🚨 Important Notes

### Camera State During Updates
- **Real-time settings**: Applied immediately, no interruption
- **Restart-required settings**: Saved to config, applied on next restart
- **Recording**: Continues during real-time updates
- **Streaming**: Continues during real-time updates

### Error Handling
- Invalid ranges return HTTP 422 with validation errors
- Camera not found returns HTTP 404
- SDK errors are logged and return HTTP 500

### Performance Impact
- **Image quality settings**: Minimal performance impact
- **Noise reduction**: May reduce FPS when enabled
- **HDR**: Significant processing overhead when enabled

This comprehensive API allows you to control all camera settings programmatically, making it perfect for integration with React dashboards or automated optimization systems!
