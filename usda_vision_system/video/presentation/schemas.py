"""
Video API Request/Response Schemas.

Pydantic models for API serialization and validation.
"""

from typing import List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field


class VideoMetadataResponse(BaseModel):
    """Video metadata response model"""
    duration_seconds: float = Field(..., description="Video duration in seconds")
    width: int = Field(..., description="Video width in pixels")
    height: int = Field(..., description="Video height in pixels")
    fps: float = Field(..., description="Video frame rate")
    codec: str = Field(..., description="Video codec")
    bitrate: Optional[int] = Field(None, description="Video bitrate in bps")
    aspect_ratio: float = Field(..., description="Video aspect ratio")
    
    class Config:
        schema_extra = {
            "example": {
                "duration_seconds": 120.5,
                "width": 1920,
                "height": 1080,
                "fps": 30.0,
                "codec": "XVID",
                "bitrate": 5000000,
                "aspect_ratio": 1.777
            }
        }


class VideoInfoResponse(BaseModel):
    """Video file information response"""
    file_id: str = Field(..., description="Unique file identifier")
    camera_name: str = Field(..., description="Camera that recorded the video")
    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Video format (avi, mp4, webm)")
    status: str = Field(..., description="Video status")
    created_at: datetime = Field(..., description="Creation timestamp")
    start_time: Optional[datetime] = Field(None, description="Recording start time")
    end_time: Optional[datetime] = Field(None, description="Recording end time")
    machine_trigger: Optional[str] = Field(None, description="Machine that triggered recording")
    metadata: Optional[VideoMetadataResponse] = Field(None, description="Video metadata")
    is_streamable: bool = Field(..., description="Whether video can be streamed")
    needs_conversion: bool = Field(..., description="Whether video needs format conversion")
    
    class Config:
        schema_extra = {
            "example": {
                "file_id": "camera1_recording_20250804_143022.avi",
                "camera_name": "camera1",
                "filename": "camera1_recording_20250804_143022.avi",
                "file_size_bytes": 52428800,
                "format": "avi",
                "status": "completed",
                "created_at": "2025-08-04T14:30:22",
                "start_time": "2025-08-04T14:30:22",
                "end_time": "2025-08-04T14:32:22",
                "machine_trigger": "vibratory_conveyor",
                "is_streamable": True,
                "needs_conversion": True
            }
        }


class VideoListResponse(BaseModel):
    """Video list response"""
    videos: List[VideoInfoResponse] = Field(..., description="List of videos")
    total_count: int = Field(..., description="Total number of videos")
    
    class Config:
        schema_extra = {
            "example": {
                "videos": [],
                "total_count": 0
            }
        }


class StreamingInfoResponse(BaseModel):
    """Streaming information response"""
    file_id: str = Field(..., description="Video file ID")
    file_size_bytes: int = Field(..., description="Total file size")
    content_type: str = Field(..., description="MIME content type")
    supports_range_requests: bool = Field(..., description="Whether range requests are supported")
    chunk_size_bytes: int = Field(..., description="Recommended chunk size for streaming")
    
    class Config:
        schema_extra = {
            "example": {
                "file_id": "camera1_recording_20250804_143022.avi",
                "file_size_bytes": 52428800,
                "content_type": "video/x-msvideo",
                "supports_range_requests": True,
                "chunk_size_bytes": 262144
            }
        }


class VideoListRequest(BaseModel):
    """Video list request parameters"""
    camera_name: Optional[str] = Field(None, description="Filter by camera name")
    start_date: Optional[datetime] = Field(None, description="Filter by start date")
    end_date: Optional[datetime] = Field(None, description="Filter by end date")
    limit: Optional[int] = Field(50, description="Maximum number of results")
    include_metadata: bool = Field(False, description="Include video metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "camera_name": "camera1",
                "start_date": "2025-08-04T00:00:00",
                "end_date": "2025-08-04T23:59:59",
                "limit": 50,
                "include_metadata": True
            }
        }


class ThumbnailRequest(BaseModel):
    """Thumbnail generation request"""
    timestamp_seconds: float = Field(1.0, description="Timestamp to extract thumbnail from")
    width: int = Field(320, description="Thumbnail width")
    height: int = Field(240, description="Thumbnail height")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp_seconds": 5.0,
                "width": 320,
                "height": 240
            }
        }
