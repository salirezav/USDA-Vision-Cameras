"""
Data models for the USDA Vision Camera System API.

This module defines Pydantic models for API requests and responses.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SystemStatusResponse(BaseModel):
    """System status response model"""

    system_started: bool
    mqtt_connected: bool
    last_mqtt_message: Optional[str] = None
    machines: Dict[str, Dict[str, Any]]
    cameras: Dict[str, Dict[str, Any]]
    active_recordings: int
    total_recordings: int
    uptime_seconds: Optional[float] = None


class MachineStatusResponse(BaseModel):
    """Machine status response model"""

    name: str
    state: str
    last_updated: str
    last_message: Optional[str] = None
    mqtt_topic: Optional[str] = None


class MQTTStatusResponse(BaseModel):
    """MQTT status response model"""

    connected: bool
    broker_host: str
    broker_port: int
    subscribed_topics: List[str]
    last_message_time: Optional[str] = None
    message_count: int
    error_count: int
    uptime_seconds: Optional[float] = None


class CameraStatusResponse(BaseModel):
    """Camera status response model"""

    name: str
    status: str
    is_recording: bool
    last_checked: str
    last_error: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    current_recording_file: Optional[str] = None
    recording_start_time: Optional[str] = None

    # Auto-recording status
    auto_recording_enabled: bool = False
    auto_recording_active: bool = False
    auto_recording_failure_count: int = 0
    auto_recording_last_attempt: Optional[str] = None
    auto_recording_last_error: Optional[str] = None


class RecordingInfoResponse(BaseModel):
    """Recording information response model"""

    camera_name: str
    filename: str
    start_time: str
    state: str
    end_time: Optional[str] = None
    file_size_bytes: Optional[int] = None
    frame_count: Optional[int] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


class StartRecordingRequest(BaseModel):
    """Start recording request model"""

    filename: Optional[str] = None
    exposure_ms: Optional[float] = Field(default=None, description="Exposure time in milliseconds")
    gain: Optional[float] = Field(default=None, description="Camera gain value")
    fps: Optional[float] = Field(default=None, description="Target frames per second")


class CameraConfigRequest(BaseModel):
    """Camera configuration update request model"""

    # Basic settings
    exposure_ms: Optional[float] = Field(default=None, ge=0.1, le=1000.0, description="Exposure time in milliseconds")
    gain: Optional[float] = Field(default=None, ge=0.0, le=20.0, description="Camera gain value")
    target_fps: Optional[float] = Field(default=None, ge=0.0, le=120.0, description="Target frames per second")

    # Image Quality Settings
    sharpness: Optional[int] = Field(default=None, ge=0, le=200, description="Sharpness (0-200, default 100)")
    contrast: Optional[int] = Field(default=None, ge=0, le=200, description="Contrast (0-200, default 100)")
    saturation: Optional[int] = Field(default=None, ge=0, le=200, description="Saturation (0-200, default 100)")
    gamma: Optional[int] = Field(default=None, ge=0, le=300, description="Gamma (0-300, default 100)")

    # Noise Reduction
    noise_filter_enabled: Optional[bool] = Field(default=None, description="Enable basic noise filtering")
    denoise_3d_enabled: Optional[bool] = Field(default=None, description="Enable advanced 3D denoising")

    # Color Settings (for color cameras)
    auto_white_balance: Optional[bool] = Field(default=None, description="Enable automatic white balance")
    color_temperature_preset: Optional[int] = Field(default=None, ge=0, le=10, description="Color temperature preset")

    # Manual White Balance RGB Gains
    wb_red_gain: Optional[float] = Field(default=None, ge=0.0, le=3.99, description="Red channel gain for manual white balance")
    wb_green_gain: Optional[float] = Field(default=None, ge=0.0, le=3.99, description="Green channel gain for manual white balance")
    wb_blue_gain: Optional[float] = Field(default=None, ge=0.0, le=3.99, description="Blue channel gain for manual white balance")

    # Advanced Settings
    anti_flicker_enabled: Optional[bool] = Field(default=None, description="Reduce artificial lighting flicker")
    light_frequency: Optional[int] = Field(default=None, ge=0, le=1, description="Light frequency (0=50Hz, 1=60Hz)")

    # HDR Settings
    hdr_enabled: Optional[bool] = Field(default=None, description="Enable High Dynamic Range")
    hdr_gain_mode: Optional[int] = Field(default=None, ge=0, le=3, description="HDR processing mode")


class CameraConfigResponse(BaseModel):
    """Camera configuration response model"""

    name: str
    machine_topic: str
    storage_path: str
    enabled: bool

    # Auto-recording settings
    auto_start_recording_enabled: bool
    auto_recording_max_retries: int
    auto_recording_retry_delay_seconds: int

    # Basic settings
    exposure_ms: float
    gain: float
    target_fps: float

    # Video recording settings
    video_format: str
    video_codec: str
    video_quality: int

    # Image Quality Settings
    sharpness: int
    contrast: int
    saturation: int
    gamma: int

    # Noise Reduction
    noise_filter_enabled: bool
    denoise_3d_enabled: bool

    # Color Settings
    auto_white_balance: bool
    color_temperature_preset: int

    # Manual White Balance RGB Gains
    wb_red_gain: float
    wb_green_gain: float
    wb_blue_gain: float

    # Advanced Settings
    anti_flicker_enabled: bool
    light_frequency: int
    bit_depth: int

    # HDR Settings
    hdr_enabled: bool
    hdr_gain_mode: int


class StartRecordingResponse(BaseModel):
    """Start recording response model"""

    success: bool
    message: str
    filename: Optional[str] = None


class StopRecordingRequest(BaseModel):
    """Stop recording request model"""

    # Note: This model is currently unused as the stop recording endpoint
    # only requires the camera_name from the URL path parameter
    pass


class StopRecordingResponse(BaseModel):
    """Stop recording response model"""

    success: bool
    message: str
    duration_seconds: Optional[float] = None


class AutoRecordingConfigRequest(BaseModel):
    """Auto-recording configuration request model"""

    enabled: bool


class AutoRecordingConfigResponse(BaseModel):
    """Auto-recording configuration response model"""

    success: bool
    message: str
    camera_name: str
    enabled: bool


class AutoRecordingStatusResponse(BaseModel):
    """Auto-recording manager status response model"""

    running: bool
    auto_recording_enabled: bool
    retry_queue: Dict[str, Any]
    enabled_cameras: List[str]


class StorageStatsResponse(BaseModel):
    """Storage statistics response model"""

    base_path: str
    total_files: int
    total_size_bytes: int
    cameras: Dict[str, Dict[str, Any]]
    disk_usage: Dict[str, Any]


class FileListRequest(BaseModel):
    """File list request model"""

    camera_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: Optional[int] = Field(default=100, le=1000)


class FileListResponse(BaseModel):
    """File list response model"""

    files: List[Dict[str, Any]]
    total_count: int


class CleanupRequest(BaseModel):
    """Cleanup request model"""

    max_age_days: Optional[int] = None


class CleanupResponse(BaseModel):
    """Cleanup response model"""

    files_removed: int
    bytes_freed: int
    errors: List[str]


class EventResponse(BaseModel):
    """Event response model"""

    event_type: str
    source: str
    data: Dict[str, Any]
    timestamp: str


class WebSocketMessage(BaseModel):
    """WebSocket message model"""

    type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str
    details: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class CameraRecoveryResponse(BaseModel):
    """Camera recovery response model"""

    success: bool
    message: str
    camera_name: str
    operation: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class CameraTestResponse(BaseModel):
    """Camera connection test response model"""

    success: bool
    message: str
    camera_name: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MQTTEventResponse(BaseModel):
    """MQTT event response model"""

    machine_name: str
    topic: str
    payload: str
    normalized_state: str
    timestamp: str
    message_number: int


class MQTTEventsHistoryResponse(BaseModel):
    """MQTT events history response model"""

    events: List[MQTTEventResponse]
    total_events: int
    last_updated: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response model"""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
