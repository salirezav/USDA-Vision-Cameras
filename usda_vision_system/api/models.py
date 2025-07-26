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
    camera_name: str
    filename: Optional[str] = None


class StartRecordingResponse(BaseModel):
    """Start recording response model"""
    success: bool
    message: str
    filename: Optional[str] = None


class StopRecordingRequest(BaseModel):
    """Stop recording request model"""
    camera_name: str


class StopRecordingResponse(BaseModel):
    """Stop recording response model"""
    success: bool
    message: str
    duration_seconds: Optional[float] = None


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


class SuccessResponse(BaseModel):
    """Success response model"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
