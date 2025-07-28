# 🤖 AI Integration Guide: USDA Vision Camera Streaming for React Projects

This guide is specifically designed for AI assistants to understand and implement the USDA Vision Camera streaming functionality in React applications.

## 📋 System Overview

The USDA Vision Camera system provides live video streaming through REST API endpoints. The streaming uses MJPEG format which is natively supported by HTML `<img>` tags and can be easily integrated into React components.

### Key Characteristics:
- **Base URL**: `http://vision:8000` (production) or `http://localhost:8000` (development)
- **Stream Format**: MJPEG (Motion JPEG)
- **Content-Type**: `multipart/x-mixed-replace; boundary=frame`
- **Authentication**: None (add if needed for production)
- **CORS**: Enabled for all origins (configure for production)

### Base URL Configuration:
- **Production**: `http://vision:8000` (requires hostname setup)
- **Development**: `http://localhost:8000` (local testing)
- **Custom IP**: `http://192.168.1.100:8000` (replace with actual IP)
- **Custom hostname**: Configure DNS or /etc/hosts as needed

## 🔌 API Endpoints Reference

### 1. Get Camera List
```http
GET /cameras
```
**Response:**
```json
{
  "camera1": {
    "name": "camera1",
    "status": "connected",
    "is_recording": false,
    "last_checked": "2025-01-28T10:30:00",
    "device_info": {...}
  },
  "camera2": {...}
}
```

### 2. Start Camera Stream
```http
POST /cameras/{camera_name}/start-stream
```
**Response:**
```json
{
  "success": true,
  "message": "Started streaming for camera camera1"
}
```

### 3. Stop Camera Stream
```http
POST /cameras/{camera_name}/stop-stream
```
**Response:**
```json
{
  "success": true,
  "message": "Stopped streaming for camera camera1"
}
```

### 4. Live Video Stream
```http
GET /cameras/{camera_name}/stream
```
**Response:** MJPEG video stream
**Usage:** Set as `src` attribute of HTML `<img>` element

## ⚛️ React Integration Examples

### Basic Camera Stream Component

```jsx
import React, { useState, useEffect } from 'react';

const CameraStream = ({ cameraName, apiBaseUrl = 'http://vision:8000' }) => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const startStream = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${apiBaseUrl}/cameras/${cameraName}/start-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        setIsStreaming(true);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to start stream');
      }
    } catch (err) {
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const stopStream = async () => {
    setLoading(true);
    
    try {
      const response = await fetch(`${apiBaseUrl}/cameras/${cameraName}/stop-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        setIsStreaming(false);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to stop stream');
      }
    } catch (err) {
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="camera-stream">
      <h3>Camera: {cameraName}</h3>
      
      {/* Video Stream */}
      <div className="stream-container">
        {isStreaming ? (
          <img
            src={`${apiBaseUrl}/cameras/${cameraName}/stream?t=${Date.now()}`}
            alt={`${cameraName} live stream`}
            style={{
              width: '100%',
              maxWidth: '640px',
              height: 'auto',
              border: '2px solid #ddd',
              borderRadius: '8px',
            }}
            onError={() => setError('Stream connection lost')}
          />
        ) : (
          <div style={{
            width: '100%',
            maxWidth: '640px',
            height: '360px',
            backgroundColor: '#f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px solid #ddd',
            borderRadius: '8px',
          }}>
            <span>No Stream Active</span>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="stream-controls" style={{ marginTop: '10px' }}>
        <button
          onClick={startStream}
          disabled={loading || isStreaming}
          style={{
            padding: '8px 16px',
            marginRight: '8px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Loading...' : 'Start Stream'}
        </button>
        
        <button
          onClick={stopStream}
          disabled={loading || !isStreaming}
          style={{
            padding: '8px 16px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Loading...' : 'Stop Stream'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          marginTop: '10px',
          padding: '8px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
        }}>
          Error: {error}
        </div>
      )}
    </div>
  );
};

export default CameraStream;
```

### Multi-Camera Dashboard Component

```jsx
import React, { useState, useEffect } from 'react';
import CameraStream from './CameraStream';

const CameraDashboard = ({ apiBaseUrl = 'http://vision:8000' }) => {
  const [cameras, setCameras] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCameras();
    
    // Refresh camera status every 30 seconds
    const interval = setInterval(fetchCameras, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchCameras = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/cameras`);
      if (response.ok) {
        const data = await response.json();
        setCameras(data);
        setError(null);
      } else {
        setError('Failed to fetch cameras');
      }
    } catch (err) {
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading cameras...</div>;
  }

  if (error) {
    return (
      <div style={{ color: 'red', padding: '20px' }}>
        Error: {error}
        <button onClick={fetchCameras} style={{ marginLeft: '10px' }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="camera-dashboard">
      <h1>USDA Vision Camera Dashboard</h1>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '20px',
        padding: '20px',
      }}>
        {Object.entries(cameras).map(([cameraName, cameraInfo]) => (
          <div key={cameraName} style={{
            border: '1px solid #ddd',
            borderRadius: '8px',
            padding: '15px',
            backgroundColor: '#f9f9f9',
          }}>
            <CameraStream 
              cameraName={cameraName} 
              apiBaseUrl={apiBaseUrl}
            />
            
            {/* Camera Status */}
            <div style={{ marginTop: '10px', fontSize: '14px' }}>
              <div>Status: <strong>{cameraInfo.status}</strong></div>
              <div>Recording: <strong>{cameraInfo.is_recording ? 'Yes' : 'No'}</strong></div>
              <div>Last Checked: {new Date(cameraInfo.last_checked).toLocaleString()}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CameraDashboard;
```

### Custom Hook for Camera Management

```jsx
import { useState, useEffect, useCallback } from 'react';

const useCameraStream = (cameraName, apiBaseUrl = 'http://vision:8000') => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startStream = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${apiBaseUrl}/cameras/${cameraName}/start-stream`, {
        method: 'POST',
      });
      
      if (response.ok) {
        setIsStreaming(true);
        return { success: true };
      } else {
        const errorData = await response.json();
        const errorMsg = errorData.detail || 'Failed to start stream';
        setError(errorMsg);
        return { success: false, error: errorMsg };
      }
    } catch (err) {
      const errorMsg = `Network error: ${err.message}`;
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  }, [cameraName, apiBaseUrl]);

  const stopStream = useCallback(async () => {
    setLoading(true);
    
    try {
      const response = await fetch(`${apiBaseUrl}/cameras/${cameraName}/stop-stream`, {
        method: 'POST',
      });
      
      if (response.ok) {
        setIsStreaming(false);
        return { success: true };
      } else {
        const errorData = await response.json();
        const errorMsg = errorData.detail || 'Failed to stop stream';
        setError(errorMsg);
        return { success: false, error: errorMsg };
      }
    } catch (err) {
      const errorMsg = `Network error: ${err.message}`;
      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  }, [cameraName, apiBaseUrl]);

  const getStreamUrl = useCallback(() => {
    return `${apiBaseUrl}/cameras/${cameraName}/stream?t=${Date.now()}`;
  }, [cameraName, apiBaseUrl]);

  return {
    isStreaming,
    loading,
    error,
    startStream,
    stopStream,
    getStreamUrl,
  };
};

export default useCameraStream;
```

## 🎨 Styling with Tailwind CSS

```jsx
const CameraStreamTailwind = ({ cameraName }) => {
  const { isStreaming, loading, error, startStream, stopStream, getStreamUrl } = useCameraStream(cameraName);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold mb-4">Camera: {cameraName}</h3>
      
      {/* Stream Container */}
      <div className="relative mb-4">
        {isStreaming ? (
          <img
            src={getStreamUrl()}
            alt={`${cameraName} live stream`}
            className="w-full max-w-2xl h-auto border-2 border-gray-300 rounded-lg"
            onError={() => setError('Stream connection lost')}
          />
        ) : (
          <div className="w-full max-w-2xl h-64 bg-gray-100 border-2 border-gray-300 rounded-lg flex items-center justify-center">
            <span className="text-gray-500">No Stream Active</span>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={startStream}
          disabled={loading || isStreaming}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Loading...' : 'Start Stream'}
        </button>
        
        <button
          onClick={stopStream}
          disabled={loading || !isStreaming}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Loading...' : 'Stop Stream'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          Error: {error}
        </div>
      )}
    </div>
  );
};
```

## 🔧 Configuration Options

### Environment Variables (.env)
```env
# Production configuration (using 'vision' hostname)
REACT_APP_CAMERA_API_URL=http://vision:8000
REACT_APP_STREAM_REFRESH_INTERVAL=30000
REACT_APP_STREAM_TIMEOUT=10000

# Development configuration (using localhost)
# REACT_APP_CAMERA_API_URL=http://localhost:8000

# Custom IP configuration
# REACT_APP_CAMERA_API_URL=http://192.168.1.100:8000
```

### API Configuration
```javascript
const apiConfig = {
  baseUrl: process.env.REACT_APP_CAMERA_API_URL || 'http://vision:8000',
  timeout: parseInt(process.env.REACT_APP_STREAM_TIMEOUT) || 10000,
  refreshInterval: parseInt(process.env.REACT_APP_STREAM_REFRESH_INTERVAL) || 30000,
};
```

### Hostname Setup Guide
```bash
# Option 1: Add to /etc/hosts (Linux/Mac)
echo "127.0.0.1 vision" | sudo tee -a /etc/hosts

# Option 2: Add to hosts file (Windows)
# Add to C:\Windows\System32\drivers\etc\hosts:
# 127.0.0.1 vision

# Option 3: Configure DNS
# Point 'vision' hostname to your server's IP address

# Verify hostname resolution
ping vision
```

## 🚨 Important Implementation Notes

### 1. MJPEG Stream Handling
- Use HTML `<img>` tag with `src` pointing to stream endpoint
- Add timestamp query parameter to prevent caching: `?t=${Date.now()}`
- Handle `onError` event for connection issues

### 2. Error Handling
- Network errors (fetch failures)
- HTTP errors (4xx, 5xx responses)
- Stream connection errors (img onError)
- Timeout handling for long requests

### 3. Performance Considerations
- Streams consume bandwidth continuously
- Stop streams when components unmount
- Limit concurrent streams based on system capacity
- Consider lazy loading for multiple cameras

### 4. State Management
- Track streaming state per camera
- Handle loading states during API calls
- Manage error states with user feedback
- Refresh camera list periodically

## 📱 Mobile Considerations

```jsx
// Responsive design for mobile
const mobileStyles = {
  container: {
    padding: '10px',
    maxWidth: '100vw',
  },
  stream: {
    width: '100%',
    maxWidth: '100vw',
    height: 'auto',
  },
  controls: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
};
```

## 🧪 Testing Integration

```javascript
// Test API connectivity
const testConnection = async () => {
  try {
    const response = await fetch(`${apiBaseUrl}/health`);
    return response.ok;
  } catch {
    return false;
  }
};

// Test camera availability
const testCamera = async (cameraName) => {
  try {
    const response = await fetch(`${apiBaseUrl}/cameras/${cameraName}/test-connection`, {
      method: 'POST',
    });
    return response.ok;
  } catch {
    return false;
  }
};
```

## 📁 Additional Files for AI Integration

### TypeScript Definitions
- `camera-api.types.ts` - Complete TypeScript definitions for all API types
- `streaming-api.http` - REST Client file with all streaming endpoints
- `STREAMING_GUIDE.md` - Comprehensive user guide for streaming functionality

### Quick Integration Checklist for AI Assistants

1. **Copy TypeScript types** from `camera-api.types.ts`
2. **Use API endpoints** from `streaming-api.http`
3. **Implement error handling** as shown in examples
4. **Add CORS configuration** if needed for production
5. **Test with multiple cameras** using provided examples

### Key Integration Points

- **Stream URL Format**: `${baseUrl}/cameras/${cameraName}/stream?t=${Date.now()}`
- **Start Stream**: `POST /cameras/{name}/start-stream`
- **Stop Stream**: `POST /cameras/{name}/stop-stream`
- **Camera List**: `GET /cameras`
- **Error Handling**: Always wrap in try-catch blocks
- **Loading States**: Implement for better UX

### Production Considerations

- Configure CORS for specific origins
- Add authentication if required
- Implement rate limiting
- Monitor system resources with multiple streams
- Add reconnection logic for network issues

This documentation provides everything an AI assistant needs to integrate the USDA Vision Camera streaming functionality into React applications, including complete code examples, error handling, and best practices.
