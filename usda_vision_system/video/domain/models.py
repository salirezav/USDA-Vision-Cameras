"""
Video Domain Models.

Pure business entities and value objects for video operations.
These models contain no external dependencies and represent core business concepts.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum


class VideoFormat(Enum):
    """Supported video formats"""
    AVI = "avi"
    MP4 = "mp4"
    WEBM = "webm"


class VideoStatus(Enum):
    """Video file status"""
    RECORDING = "recording"
    COMPLETED = "completed"
    PROCESSING = "processing"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class VideoMetadata:
    """Video metadata value object"""
    duration_seconds: float
    width: int
    height: int
    fps: float
    codec: str
    bitrate: Optional[int] = None
    
    @property
    def resolution(self) -> Tuple[int, int]:
        """Get video resolution as tuple"""
        return (self.width, self.height)
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio"""
        return self.width / self.height if self.height > 0 else 0.0


@dataclass(frozen=True)
class StreamRange:
    """HTTP range request value object"""
    start: int
    end: Optional[int] = None
    
    def __post_init__(self):
        if self.start < 0:
            raise ValueError("Start byte cannot be negative")
        if self.end is not None and self.end < self.start:
            raise ValueError("End byte cannot be less than start byte")
    
    @property
    def size(self) -> Optional[int]:
        """Get range size in bytes"""
        if self.end is not None:
            return self.end - self.start + 1
        return None
    
    @classmethod
    def from_header(cls, range_header: str, file_size: int) -> 'StreamRange':
        """Parse HTTP Range header"""
        if not range_header.startswith('bytes='):
            raise ValueError("Invalid range header format")
        
        range_spec = range_header[6:]  # Remove 'bytes='
        
        if '-' not in range_spec:
            raise ValueError("Invalid range specification")
        
        start_str, end_str = range_spec.split('-', 1)
        
        if start_str:
            start = int(start_str)
        else:
            # Suffix range (e.g., "-500" means last 500 bytes)
            if not end_str:
                raise ValueError("Invalid range specification")
            suffix_length = int(end_str)
            start = max(0, file_size - suffix_length)
            end = file_size - 1
            return cls(start=start, end=end)
        
        if end_str:
            end = min(int(end_str), file_size - 1)
        else:
            end = file_size - 1
        
        return cls(start=start, end=end)


@dataclass
class VideoFile:
    """Video file entity"""
    file_id: str
    camera_name: str
    filename: str
    file_path: Path
    file_size_bytes: int
    created_at: datetime
    status: VideoStatus
    format: VideoFormat
    metadata: Optional[VideoMetadata] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    machine_trigger: Optional[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate video file data"""
        if not self.file_id:
            raise ValueError("File ID cannot be empty")
        if not self.camera_name:
            raise ValueError("Camera name cannot be empty")
        if self.file_size_bytes < 0:
            raise ValueError("File size cannot be negative")
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get video duration from metadata"""
        return self.metadata.duration_seconds if self.metadata else None
    
    @property
    def is_streamable(self) -> bool:
        """Check if video can be streamed"""
        return (
            self.status in [VideoStatus.COMPLETED, VideoStatus.RECORDING] and
            self.file_path.exists() and
            self.file_size_bytes > 0
        )
    
    @property
    def web_compatible_format(self) -> VideoFormat:
        """Get web-compatible format for this video"""
        # AVI files should be converted to MP4 for web compatibility
        if self.format == VideoFormat.AVI:
            return VideoFormat.MP4
        return self.format
    
    def needs_conversion(self) -> bool:
        """Check if video needs format conversion for web streaming"""
        return self.format != self.web_compatible_format
    
    def get_converted_filename(self) -> str:
        """Get filename for converted version"""
        if not self.needs_conversion():
            return self.filename
        
        # Replace extension with web-compatible format
        stem = Path(self.filename).stem
        return f"{stem}.{self.web_compatible_format.value}"
