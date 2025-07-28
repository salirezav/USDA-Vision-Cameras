/**
 * TypeScript definitions for USDA Vision Camera System API
 * 
 * This file provides complete type definitions for AI assistants
 * to integrate the camera streaming functionality into React/TypeScript projects.
 */

// =============================================================================
// BASE CONFIGURATION
// =============================================================================

export interface ApiConfig {
  baseUrl: string;
  timeout?: number;
  refreshInterval?: number;
}

export const defaultApiConfig: ApiConfig = {
  baseUrl: 'http://vision:8000',  // Production default, change to 'http://localhost:8000' for development
  timeout: 10000,
  refreshInterval: 30000,
};

// =============================================================================
// CAMERA TYPES
// =============================================================================

export interface CameraDeviceInfo {
  friendly_name?: string;
  port_type?: string;
  serial_number?: string;
  device_index?: number;
  error?: string;
}

export interface CameraInfo {
  name: string;
  status: 'connected' | 'disconnected' | 'error' | 'not_found' | 'available';
  is_recording: boolean;
  last_checked: string; // ISO date string
  last_error?: string | null;
  device_info?: CameraDeviceInfo;
  current_recording_file?: string | null;
  recording_start_time?: string | null; // ISO date string
}

export interface CameraListResponse {
  [cameraName: string]: CameraInfo;
}

// =============================================================================
// STREAMING TYPES
// =============================================================================

export interface StreamStartRequest {
  // No body required - camera name is in URL path
}

export interface StreamStartResponse {
  success: boolean;
  message: string;
}

export interface StreamStopRequest {
  // No body required - camera name is in URL path
}

export interface StreamStopResponse {
  success: boolean;
  message: string;
}

export interface StreamStatus {
  isStreaming: boolean;
  streamUrl?: string;
  error?: string;
}

// =============================================================================
// RECORDING TYPES
// =============================================================================

export interface StartRecordingRequest {
  filename?: string;
  exposure_ms?: number;
  gain?: number;
  fps?: number;
}

export interface StartRecordingResponse {
  success: boolean;
  message: string;
  filename?: string;
}

export interface StopRecordingResponse {
  success: boolean;
  message: string;
}

// =============================================================================
// SYSTEM TYPES
// =============================================================================

export interface SystemStatusResponse {
  status: string;
  uptime: string;
  api_server_running: boolean;
  camera_manager_running: boolean;
  mqtt_client_connected: boolean;
  total_cameras: number;
  active_recordings: number;
  active_streams?: number;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
}

// =============================================================================
// ERROR TYPES
// =============================================================================

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface StreamError extends Error {
  type: 'network' | 'api' | 'stream' | 'timeout';
  cameraName: string;
  originalError?: Error;
}

// =============================================================================
// HOOK TYPES
// =============================================================================

export interface UseCameraStreamResult {
  isStreaming: boolean;
  loading: boolean;
  error: string | null;
  startStream: () => Promise<{ success: boolean; error?: string }>;
  stopStream: () => Promise<{ success: boolean; error?: string }>;
  getStreamUrl: () => string;
  refreshStream: () => void;
}

export interface UseCameraListResult {
  cameras: CameraListResponse;
  loading: boolean;
  error: string | null;
  refreshCameras: () => Promise<void>;
}

export interface UseCameraRecordingResult {
  isRecording: boolean;
  loading: boolean;
  error: string | null;
  currentFile: string | null;
  startRecording: (options?: StartRecordingRequest) => Promise<{ success: boolean; error?: string }>;
  stopRecording: () => Promise<{ success: boolean; error?: string }>;
}

// =============================================================================
// COMPONENT PROPS TYPES
// =============================================================================

export interface CameraStreamProps {
  cameraName: string;
  apiConfig?: ApiConfig;
  autoStart?: boolean;
  onStreamStart?: (cameraName: string) => void;
  onStreamStop?: (cameraName: string) => void;
  onError?: (error: StreamError) => void;
  className?: string;
  style?: React.CSSProperties;
}

export interface CameraDashboardProps {
  apiConfig?: ApiConfig;
  cameras?: string[]; // If provided, only show these cameras
  showRecordingControls?: boolean;
  showStreamingControls?: boolean;
  refreshInterval?: number;
  onCameraSelect?: (cameraName: string) => void;
  className?: string;
}

export interface CameraControlsProps {
  cameraName: string;
  apiConfig?: ApiConfig;
  showRecording?: boolean;
  showStreaming?: boolean;
  onAction?: (action: 'start-stream' | 'stop-stream' | 'start-recording' | 'stop-recording', cameraName: string) => void;
}

// =============================================================================
// API CLIENT TYPES
// =============================================================================

export interface CameraApiClient {
  // System endpoints
  getHealth(): Promise<HealthResponse>;
  getSystemStatus(): Promise<SystemStatusResponse>;

  // Camera endpoints
  getCameras(): Promise<CameraListResponse>;
  getCameraStatus(cameraName: string): Promise<CameraInfo>;
  testCameraConnection(cameraName: string): Promise<{ success: boolean; message: string }>;

  // Streaming endpoints
  startStream(cameraName: string): Promise<StreamStartResponse>;
  stopStream(cameraName: string): Promise<StreamStopResponse>;
  getStreamUrl(cameraName: string): string;

  // Recording endpoints
  startRecording(cameraName: string, options?: StartRecordingRequest): Promise<StartRecordingResponse>;
  stopRecording(cameraName: string): Promise<StopRecordingResponse>;
}

// =============================================================================
// UTILITY TYPES
// =============================================================================

export type CameraAction = 'start-stream' | 'stop-stream' | 'start-recording' | 'stop-recording' | 'test-connection';

export interface CameraActionResult {
  success: boolean;
  message: string;
  error?: string;
}

export interface StreamingState {
  [cameraName: string]: {
    isStreaming: boolean;
    isLoading: boolean;
    error: string | null;
    lastStarted?: Date;
  };
}

export interface RecordingState {
  [cameraName: string]: {
    isRecording: boolean;
    isLoading: boolean;
    error: string | null;
    currentFile: string | null;
    startTime?: Date;
  };
}

// =============================================================================
// EVENT TYPES
// =============================================================================

export interface CameraEvent {
  type: 'stream-started' | 'stream-stopped' | 'stream-error' | 'recording-started' | 'recording-stopped' | 'recording-error';
  cameraName: string;
  timestamp: Date;
  data?: any;
}

export type CameraEventHandler = (event: CameraEvent) => void;

// =============================================================================
// CONFIGURATION TYPES
// =============================================================================

export interface StreamConfig {
  fps: number;
  quality: number; // 1-100
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}

export interface CameraStreamConfig extends StreamConfig {
  cameraName: string;
  autoReconnect: boolean;
  maxReconnectAttempts: number;
}

// =============================================================================
// CONTEXT TYPES (for React Context)
// =============================================================================

export interface CameraContextValue {
  cameras: CameraListResponse;
  streamingState: StreamingState;
  recordingState: RecordingState;
  apiClient: CameraApiClient;

  // Actions
  startStream: (cameraName: string) => Promise<CameraActionResult>;
  stopStream: (cameraName: string) => Promise<CameraActionResult>;
  startRecording: (cameraName: string, options?: StartRecordingRequest) => Promise<CameraActionResult>;
  stopRecording: (cameraName: string) => Promise<CameraActionResult>;
  refreshCameras: () => Promise<void>;

  // State
  loading: boolean;
  error: string | null;
}

// =============================================================================
// EXAMPLE USAGE TYPES
// =============================================================================

/**
 * Example usage in React component:
 * 
 * ```typescript
 * import { CameraStreamProps, UseCameraStreamResult } from './camera-api.types';
 * 
 * const CameraStream: React.FC<CameraStreamProps> = ({ 
 *   cameraName, 
 *   apiConfig = defaultApiConfig,
 *   autoStart = false,
 *   onStreamStart,
 *   onStreamStop,
 *   onError 
 * }) => {
 *   const {
 *     isStreaming,
 *     loading,
 *     error,
 *     startStream,
 *     stopStream,
 *     getStreamUrl
 *   }: UseCameraStreamResult = useCameraStream(cameraName, apiConfig);
 * 
 *   // Component implementation...
 * };
 * ```
 */

/**
 * Example API client usage:
 * 
 * ```typescript
 * const apiClient: CameraApiClient = new CameraApiClientImpl(defaultApiConfig);
 * 
 * // Start streaming
 * const result = await apiClient.startStream('camera1');
 * if (result.success) {
 *   const streamUrl = apiClient.getStreamUrl('camera1');
 *   // Use streamUrl in img tag
 * }
 * ```
 */

/**
 * Example hook usage:
 * 
 * ```typescript
 * const MyComponent = () => {
 *   const { cameras, loading, error, refreshCameras } = useCameraList();
 *   const { isStreaming, startStream, stopStream } = useCameraStream('camera1');
 *   
 *   // Component logic...
 * };
 * ```
 */

export default {};
