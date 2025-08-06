# Camera Recovery and Diagnostics Guide

This guide explains the new camera recovery functionality implemented in the USDA Vision Camera System API.

## Overview

The system now includes comprehensive camera recovery capabilities to handle connection issues, initialization failures, and other camera-related problems. These features use the underlying mvsdk (python demo) library functions to perform various recovery operations.

## Available Recovery Operations

### 1. Connection Test (`/cameras/{camera_name}/test-connection`)
- **Purpose**: Test if the camera connection is working
- **SDK Function**: `CameraConnectTest()`
- **Use Case**: Diagnose connection issues
- **HTTP Method**: POST
- **Response**: `CameraTestResponse`

### 2. Reconnect (`/cameras/{camera_name}/reconnect`)
- **Purpose**: Soft reconnection to the camera
- **SDK Function**: `CameraReConnect()`
- **Use Case**: Most common fix for connection issues
- **HTTP Method**: POST
- **Response**: `CameraRecoveryResponse`

### 3. Restart Grab (`/cameras/{camera_name}/restart-grab`)
- **Purpose**: Restart the camera grab process
- **SDK Function**: `CameraRestartGrab()`
- **Use Case**: Fix issues with image capture
- **HTTP Method**: POST
- **Response**: `CameraRecoveryResponse`

### 4. Reset Timestamp (`/cameras/{camera_name}/reset-timestamp`)
- **Purpose**: Reset camera timestamp
- **SDK Function**: `CameraRstTimeStamp()`
- **Use Case**: Fix timing-related issues
- **HTTP Method**: POST
- **Response**: `CameraRecoveryResponse`

### 5. Full Reset (`/cameras/{camera_name}/full-reset`)
- **Purpose**: Complete camera reset (uninitialize and reinitialize)
- **SDK Functions**: `CameraUnInit()` + `CameraInit()`
- **Use Case**: Hard reset for persistent issues
- **HTTP Method**: POST
- **Response**: `CameraRecoveryResponse`

### 6. Reinitialize (`/cameras/{camera_name}/reinitialize`)
- **Purpose**: Reinitialize cameras that failed initial setup
- **SDK Functions**: Complete recorder recreation
- **Use Case**: Cameras that never initialized properly
- **HTTP Method**: POST
- **Response**: `CameraRecoveryResponse`

## Recommended Troubleshooting Workflow

When a camera has issues, follow this order:

1. **Test Connection** - Diagnose the problem
   ```http
   POST http://localhost:8000/cameras/camera1/test-connection
   ```

2. **Try Reconnect** - Most common fix
   ```http
   POST http://localhost:8000/cameras/camera1/reconnect
   ```

3. **Restart Grab** - If reconnect doesn't work
   ```http
   POST http://localhost:8000/cameras/camera1/restart-grab
   ```

4. **Full Reset** - For persistent issues
   ```http
   POST http://localhost:8000/cameras/camera1/full-reset
   ```

5. **Reinitialize** - For cameras that never worked
   ```http
   POST http://localhost:8000/cameras/camera1/reinitialize
   ```

## Response Format

All recovery operations return structured responses:

### CameraTestResponse
```json
{
  "success": true,
  "message": "Camera camera1 connection test passed",
  "camera_name": "camera1",
  "timestamp": "2024-01-01T12:00:00"
}
```

### CameraRecoveryResponse
```json
{
  "success": true,
  "message": "Camera camera1 reconnected successfully",
  "camera_name": "camera1",
  "operation": "reconnect",
  "timestamp": "2024-01-01T12:00:00"
}
```

## Implementation Details

### CameraRecorder Methods
- `test_connection()`: Tests camera connection
- `reconnect()`: Performs soft reconnection
- `restart_grab()`: Restarts grab process
- `reset_timestamp()`: Resets timestamp
- `full_reset()`: Complete reset with cleanup and reinitialization

### CameraManager Methods
- `test_camera_connection(camera_name)`: Test specific camera
- `reconnect_camera(camera_name)`: Reconnect specific camera
- `restart_camera_grab(camera_name)`: Restart grab for specific camera
- `reset_camera_timestamp(camera_name)`: Reset timestamp for specific camera
- `full_reset_camera(camera_name)`: Full reset for specific camera
- `reinitialize_failed_camera(camera_name)`: Reinitialize failed camera

### State Management
All recovery operations automatically update the camera status in the state manager:
- Success: Status set to "connected"
- Failure: Status set to appropriate error state with error message

## Error Handling

The system includes comprehensive error handling:
- SDK exceptions are caught and logged
- State manager is updated with error information
- Proper HTTP status codes are returned
- Detailed error messages are provided

## Testing

Use the provided test files:
- `api-tests.http`: Manual API testing with VS Code REST Client
- `test_camera_recovery_api.py`: Automated testing script

## Safety Features

- Recording is automatically stopped before recovery operations
- Camera resources are properly cleaned up
- Thread-safe operations with proper locking
- Graceful error handling prevents system crashes

## Common Use Cases

1. **Camera Lost Connection**: Use reconnect
2. **Camera Won't Capture**: Use restart-grab
3. **Camera Initialization Failed**: Use reinitialize
4. **Persistent Issues**: Use full-reset
5. **Timing Problems**: Use reset-timestamp

This recovery system provides robust tools to handle most camera-related issues without requiring system restart or manual intervention.
