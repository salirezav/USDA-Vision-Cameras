# Instructions for AI Agent: Auto-Recording Feature Integration

## 🎯 Task Overview
Update the React application to support the new auto-recording feature that has been added to the USDA Vision Camera System backend.

## 📋 What You Need to Know

### System Context
- **Camera 1** monitors the **vibratory conveyor** (conveyor/cracker cam)
- **Camera 2** monitors the **blower separator** machine
- Auto-recording automatically starts when machines turn ON and stops when they turn OFF
- The system includes retry logic for failed recording attempts
- Manual recording always takes precedence over auto-recording

### New Backend Capabilities
The backend now supports:
1. **Automatic recording** triggered by MQTT machine state changes
2. **Retry mechanism** for failed recording attempts (configurable retries and delays)
3. **Status tracking** for auto-recording state, failures, and attempts
4. **API endpoints** for enabling/disabling and monitoring auto-recording

## 🔧 Required React App Changes

### 1. Update TypeScript Interfaces

Add these new fields to existing `CameraStatusResponse`:
```typescript
interface CameraStatusResponse {
  // ... existing fields
  auto_recording_enabled: boolean;
  auto_recording_active: boolean;
  auto_recording_failure_count: number;
  auto_recording_last_attempt?: string;
  auto_recording_last_error?: string;
}
```

Add new response types:
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

### 2. Add New API Endpoints

```typescript
// Enable auto-recording for a camera
POST /cameras/{camera_name}/auto-recording/enable

// Disable auto-recording for a camera  
POST /cameras/{camera_name}/auto-recording/disable

// Get overall auto-recording system status
GET /auto-recording/status
```

### 3. UI Components to Add/Update

#### Camera Status Display
- Add auto-recording status badge/indicator
- Show auto-recording enabled/disabled state
- Display failure count if > 0
- Show last error message if any
- Distinguish between manual and auto-recording states

#### Auto-Recording Controls
- Toggle switch to enable/disable auto-recording per camera
- System-wide auto-recording status display
- Retry queue information
- Machine state correlation display

#### Error Handling
- Clear display of auto-recording failures
- Retry attempt information
- Last attempt timestamp
- Quick retry/reset actions

### 4. Visual Design Guidelines

**Status Priority (highest to lowest):**
1. Manual Recording (red/prominent) - user initiated
2. Auto-Recording Active (green) - machine ON, recording
3. Auto-Recording Enabled (blue) - ready but machine OFF
4. Auto-Recording Disabled (gray) - feature disabled

**Machine Correlation:**
- Show machine name next to camera (e.g., "Vibratory Conveyor", "Blower Separator")
- Display machine ON/OFF status
- Alert if machine is ON but auto-recording failed

## 🎨 Specific Implementation Tasks

### Task 1: Update Camera Cards
- Add auto-recording status indicators
- Add enable/disable toggle controls
- Show machine state correlation
- Display failure information when relevant

### Task 2: Create Auto-Recording Dashboard
- Overall system status
- List of enabled cameras
- Active retry queue display
- Recent events/errors

### Task 3: Update Recording Status Logic
- Distinguish between manual and auto-recording
- Show appropriate controls based on recording type
- Handle manual override scenarios

### Task 4: Add Error Handling
- Display auto-recording failures clearly
- Show retry attempts and timing
- Provide manual retry options

## 📱 User Experience Requirements

### Key Behaviors
1. **Non-Intrusive:** Auto-recording status shouldn't clutter the main interface
2. **Clear Hierarchy:** Manual controls should be more prominent than auto-recording
3. **Informative:** Users should understand why recording started/stopped
4. **Actionable:** Clear options to enable/disable or retry failed attempts

### Mobile Considerations
- Auto-recording controls should work well on mobile
- Status information should be readable on small screens
- Consider collapsible sections for detailed information

## 🔍 Testing Requirements

Ensure the React app correctly handles:
- [ ] Toggling auto-recording on/off per camera
- [ ] Displaying real-time status updates
- [ ] Showing error states and retry information
- [ ] Manual recording override scenarios
- [ ] Machine state changes and correlation
- [ ] Mobile interface functionality

## 📚 Reference Files

Key files to review for implementation details:
- `AUTO_RECORDING_FEATURE_GUIDE.md` - Comprehensive technical details
- `api-endpoints.http` - API endpoint documentation
- `config.json` - Configuration structure
- `usda_vision_system/api/models.py` - Response type definitions

## 🎯 Success Criteria

The React app should:
1. **Display** auto-recording status for each camera clearly
2. **Allow** users to enable/disable auto-recording per camera
3. **Show** machine state correlation and recording triggers
4. **Handle** error states and retry scenarios gracefully
5. **Maintain** existing manual recording functionality
6. **Provide** clear visual hierarchy between manual and auto-recording

## 💡 Implementation Tips

1. **Start Small:** Begin with basic status display, then add controls
2. **Use Existing Patterns:** Follow the current app's design patterns
3. **Test Incrementally:** Test each feature as you add it
4. **Consider State Management:** Update your state management to handle new data
5. **Mobile First:** Ensure mobile usability from the start

The goal is to seamlessly integrate auto-recording capabilities while maintaining the existing user experience and adding valuable automation features for the camera operators.
