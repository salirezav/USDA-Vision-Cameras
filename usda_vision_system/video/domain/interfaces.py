"""
Video Domain Interfaces.

Abstract interfaces that define contracts for video operations.
These interfaces allow dependency inversion - domain logic doesn't depend on infrastructure.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, BinaryIO
from datetime import datetime
from pathlib import Path

from .models import VideoFile, VideoMetadata, StreamRange, VideoFormat


class VideoRepository(ABC):
    """Abstract repository for video file access"""
    
    @abstractmethod
    async def get_by_id(self, file_id: str) -> Optional[VideoFile]:
        """Get video file by ID"""
        pass
    
    @abstractmethod
    async def get_by_camera(
        self, 
        camera_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[VideoFile]:
        """Get video files for a camera with optional filters"""
        pass
    
    @abstractmethod
    async def get_all(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[VideoFile]:
        """Get all video files with optional filters"""
        pass
    
    @abstractmethod
    async def exists(self, file_id: str) -> bool:
        """Check if video file exists"""
        pass
    
    @abstractmethod
    async def get_file_stream(self, video_file: VideoFile) -> BinaryIO:
        """Get file stream for reading video data"""
        pass
    
    @abstractmethod
    async def get_file_range(
        self, 
        video_file: VideoFile, 
        range_request: StreamRange
    ) -> bytes:
        """Get specific byte range from video file"""
        pass


class VideoConverter(ABC):
    """Abstract video format converter"""
    
    @abstractmethod
    async def convert(
        self,
        source_path: Path,
        target_path: Path,
        target_format: VideoFormat,
        quality: Optional[str] = None
    ) -> bool:
        """Convert video to target format"""
        pass
    
    @abstractmethod
    async def is_conversion_needed(
        self,
        source_format: VideoFormat,
        target_format: VideoFormat
    ) -> bool:
        """Check if conversion is needed"""
        pass
    
    @abstractmethod
    async def get_converted_path(
        self,
        original_path: Path,
        target_format: VideoFormat
    ) -> Path:
        """Get path for converted file"""
        pass
    
    @abstractmethod
    async def cleanup_converted_files(self, max_age_hours: int = 24) -> int:
        """Clean up old converted files"""
        pass


class MetadataExtractor(ABC):
    """Abstract video metadata extractor"""
    
    @abstractmethod
    async def extract(self, file_path: Path) -> Optional[VideoMetadata]:
        """Extract metadata from video file"""
        pass
    
    @abstractmethod
    async def extract_thumbnail(
        self,
        file_path: Path,
        timestamp_seconds: float = 1.0,
        size: tuple = (320, 240)
    ) -> Optional[bytes]:
        """Extract thumbnail image from video"""
        pass
    
    @abstractmethod
    async def is_valid_video(self, file_path: Path) -> bool:
        """Check if file is a valid video"""
        pass


class StreamingCache(ABC):
    """Abstract cache for streaming optimization"""
    
    @abstractmethod
    async def get_cached_range(
        self,
        file_id: str,
        range_request: StreamRange
    ) -> Optional[bytes]:
        """Get cached byte range"""
        pass
    
    @abstractmethod
    async def cache_range(
        self,
        file_id: str,
        range_request: StreamRange,
        data: bytes
    ) -> None:
        """Cache byte range data"""
        pass
    
    @abstractmethod
    async def invalidate_file(self, file_id: str) -> None:
        """Invalidate all cached data for a file"""
        pass
    
    @abstractmethod
    async def cleanup_cache(self, max_size_mb: int = 100) -> int:
        """Clean up cache to stay under size limit"""
        pass
