# Auto-Recording Feature Implementation Guide

## 🎯 Overview for React App Development

This document provides a comprehensive guide for updating the React application to support the new auto-recording feature that was added to the USDA Vision Camera System.

## 📋 What Changed in the Backend

### New API Endpoints Added

1. **Enable Auto-Recording**
   ```http
   POST /cameras/{camera_name}/auto-recording/enable
   Response: AutoRecordingConfigResponse
   ```

2. **Disable Auto-Recording**
   ```http
   POST /cameras/{camera_name}/auto-recording/disable
   Response: AutoRecordingConfigResponse
   ```

3. **Get Auto-Recording Status**
   ```http
   GET /auto-recording/status
   Response: AutoRecordingStatusResponse
   ```

### Updated API Responses

#### CameraStatusResponse (Updated)
```typescript
interface CameraStatusResponse {
  name: string;
  status: string;
  is_recording: boolean;
  last_checked: string;
  last_error?: string;
  device_info?: any;
  current_recording_file?: string;
  recording_start_time?: string;
  
  // NEW AUTO-RECORDING FIELDS
  auto_recording_enabled: boolean;
  auto_recording_active: boolean;
  auto_recording_failure_count: number;
  auto_recording_last_attempt?: string;
  auto_recording_last_error?: string;
}
```

#### CameraConfigResponse (Updated)
```typescript
interface CameraConfigResponse {
  name: string;
  machine_topic: string;
  storage_path: string;
  enabled: boolean;
  
  // NEW AUTO-RECORDING CONFIG FIELDS
  auto_start_recording_enabled: boolean;
  auto_recording_max_retries: number;
  auto_recording_retry_delay_seconds: number;
  
  // ... existing fields (exposure_ms, gain, etc.)
}
```

#### New Response Types
```typescript
interface AutoRecordingConfigResponse {
  success: boolean;
  message: string;
  camera_name: string;
  enabled: boolean;
}

interface AutoRecordingStatusResponse {
  running: boolean;
  auto_recording_enabled: boolean;
  retry_queue: Record<string, any>;
  enabled_cameras: string[];
}
```

## 🎨 React App UI Requirements

### 1. Camera Status Display Updates

**Add to Camera Cards/Components:**
- Auto-recording enabled/disabled indicator
- Auto-recording active status (when machine is ON and auto-recording)
- Failure count display (if > 0)
- Last auto-recording error (if any)
- Visual distinction between manual and auto-recording

**Example UI Elements:**
```jsx
// Auto-recording status badge
{camera.auto_recording_enabled && (
  <Badge variant={camera.auto_recording_active ? "success" : "secondary"}>
    Auto-Recording {camera.auto_recording_active ? "Active" : "Enabled"}
  </Badge>
)}

// Failure indicator
{camera.auto_recording_failure_count > 0 && (
  <Alert variant="warning">
    Auto-recording failures: {camera.auto_recording_failure_count}
  </Alert>
)}
```

### 2. Auto-Recording Controls

**Add Toggle Controls:**
- Enable/Disable auto-recording per camera
- Global auto-recording status display
- Retry queue monitoring

**Example Control Component:**
```jsx
const AutoRecordingToggle = ({ camera, onToggle }) => {
  const handleToggle = async () => {
    const endpoint = camera.auto_recording_enabled ? 'disable' : 'enable';
    await fetch(`/cameras/${camera.name}/auto-recording/${endpoint}`, {
      method: 'POST'
    });
    onToggle();
  };

  return (
    <Switch
      checked={camera.auto_recording_enabled}
      onChange={handleToggle}
      label="Auto-Recording"
    />
  );
};
```

### 3. Machine State Integration

**Display Machine Status:**
- Show which machine each camera monitors
- Display current machine state (ON/OFF)
- Show correlation between machine state and recording status

**Camera-Machine Mapping:**
- Camera 1 → Vibratory Conveyor (conveyor/cracker cam)
- Camera 2 → Blower Separator (blower separator)

### 4. Auto-Recording Dashboard

**Create New Dashboard Section:**
- Overall auto-recording system status
- List of cameras with auto-recording enabled
- Active retry queue display
- Recent auto-recording events/logs

## 🔧 Implementation Steps for React App

### Step 1: Update TypeScript Interfaces
```typescript
// Update existing interfaces in your types file
// Add new interfaces for auto-recording responses
```

### Step 2: Update API Service Functions
```typescript
// Add new API calls
export const enableAutoRecording = (cameraName: string) =>
  fetch(`/cameras/${cameraName}/auto-recording/enable`, { method: 'POST' });

export const disableAutoRecording = (cameraName: string) =>
  fetch(`/cameras/${cameraName}/auto-recording/disable`, { method: 'POST' });

export const getAutoRecordingStatus = () =>
  fetch('/auto-recording/status').then(res => res.json());
```

### Step 3: Update Camera Components
- Add auto-recording status indicators
- Add enable/disable controls
- Update recording status display to distinguish auto vs manual

### Step 4: Create Auto-Recording Management Panel
- System-wide auto-recording status
- Per-camera auto-recording controls
- Retry queue monitoring
- Error reporting and alerts

### Step 5: Update State Management
```typescript
// Add auto-recording state to your store/context
interface AppState {
  cameras: CameraStatusResponse[];
  autoRecordingStatus: AutoRecordingStatusResponse;
  // ... existing state
}
```

## 🎯 Key User Experience Considerations

### Visual Indicators
1. **Recording Status Hierarchy:**
   - Manual Recording (highest priority - red/prominent)
   - Auto-Recording Active (green/secondary)
   - Auto-Recording Enabled but Inactive (blue/subtle)
   - Auto-Recording Disabled (gray/muted)

2. **Machine State Correlation:**
   - Show machine ON/OFF status next to camera
   - Indicate when auto-recording should be active
   - Alert if machine is ON but auto-recording failed

3. **Error Handling:**
   - Clear error messages for auto-recording failures
   - Retry count display
   - Last attempt timestamp
   - Quick retry/reset options

### User Controls
1. **Quick Actions:**
   - Toggle auto-recording per camera
   - Force retry failed auto-recording
   - Override auto-recording (manual control)

2. **Configuration:**
   - Adjust retry settings
   - Change machine-camera mappings
   - Set recording parameters for auto-recording

## 🚨 Important Notes

### Behavior Rules
1. **Manual Override:** Manual recording always takes precedence over auto-recording
2. **Non-Blocking:** Auto-recording status checks don't interfere with camera operation
3. **Machine Correlation:** Auto-recording only activates when the associated machine turns ON
4. **Failure Handling:** Failed auto-recording attempts are retried automatically with exponential backoff

### API Polling Recommendations
- Poll camera status every 2-3 seconds for real-time updates
- Poll auto-recording status every 5-10 seconds
- Use WebSocket connections if available for real-time machine state updates

## 📱 Mobile Considerations
- Auto-recording controls should be easily accessible on mobile
- Status indicators should be clear and readable on small screens
- Consider collapsible sections for detailed auto-recording information

## 🔍 Testing Checklist
- [ ] Auto-recording toggle works for each camera
- [ ] Status updates reflect machine state changes
- [ ] Error states are clearly displayed
- [ ] Manual recording overrides auto-recording
- [ ] Retry mechanism is visible to users
- [ ] Mobile interface is functional

This guide provides everything needed to update the React app to fully support the new auto-recording feature!
