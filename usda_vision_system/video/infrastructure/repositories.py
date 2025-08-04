"""
Video Repository Implementations.

File system-based implementation of video repository interface.
"""

import asyncio
import logging
from typing import List, Optional, BinaryIO
from datetime import datetime
from pathlib import Path
import aiofiles

from ..domain.interfaces import VideoRepository
from ..domain.models import VideoFile, VideoFormat, VideoStatus, StreamRange
from ...core.config import Config
from ...storage.manager import StorageManager


class FileSystemVideoRepository(VideoRepository):
    """File system implementation of video repository"""
    
    def __init__(self, config: Config, storage_manager: StorageManager):
        self.config = config
        self.storage_manager = storage_manager
        self.logger = logging.getLogger(__name__)
    
    async def get_by_id(self, file_id: str) -> Optional[VideoFile]:
        """Get video file by ID"""
        try:
            # Get file info from storage manager
            file_info = self.storage_manager.get_file_info(file_id)
            if not file_info:
                return None
            
            return self._convert_to_video_file(file_info)
        
        except Exception as e:
            self.logger.error(f"Error getting video by ID {file_id}: {e}")
            return None
    
    async def get_by_camera(
        self,
        camera_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[VideoFile]:
        """Get video files for a camera with optional filters"""
        try:
            # Use storage manager to get files
            files = self.storage_manager.get_recording_files(
                camera_name=camera_name,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            return [self._convert_to_video_file(file_info) for file_info in files]
        
        except Exception as e:
            self.logger.error(f"Error getting videos for camera {camera_name}: {e}")
            return []
    
    async def get_all(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[VideoFile]:
        """Get all video files with optional filters"""
        try:
            # Get files from all cameras
            files = self.storage_manager.get_recording_files(
                camera_name=None,  # All cameras
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            return [self._convert_to_video_file(file_info) for file_info in files]
        
        except Exception as e:
            self.logger.error(f"Error getting all videos: {e}")
            return []
    
    async def exists(self, file_id: str) -> bool:
        """Check if video file exists"""
        try:
            video_file = await self.get_by_id(file_id)
            return video_file is not None and video_file.file_path.exists()
        
        except Exception as e:
            self.logger.error(f"Error checking if video exists {file_id}: {e}")
            return False
    
    async def get_file_stream(self, video_file: VideoFile) -> BinaryIO:
        """Get file stream for reading video data"""
        try:
            # Use aiofiles for async file operations
            return await aiofiles.open(video_file.file_path, 'rb')
        
        except Exception as e:
            self.logger.error(f"Error opening file stream for {video_file.file_id}: {e}")
            raise
    
    async def get_file_range(
        self,
        video_file: VideoFile,
        range_request: StreamRange
    ) -> bytes:
        """Get specific byte range from video file"""
        try:
            async with aiofiles.open(video_file.file_path, 'rb') as f:
                # Seek to start position
                await f.seek(range_request.start)
                
                # Calculate how many bytes to read
                if range_request.end is not None:
                    bytes_to_read = range_request.end - range_request.start + 1
                    data = await f.read(bytes_to_read)
                else:
                    # Read to end of file
                    data = await f.read()
                
                return data
        
        except Exception as e:
            self.logger.error(f"Error reading file range for {video_file.file_id}: {e}")
            raise
    
    def _convert_to_video_file(self, file_info: dict) -> VideoFile:
        """Convert storage manager file info to VideoFile domain model"""
        try:
            file_path = Path(file_info["filename"])
            
            # Determine video format from extension
            extension = file_path.suffix.lower().lstrip('.')
            if extension == 'avi':
                format = VideoFormat.AVI
            elif extension == 'mp4':
                format = VideoFormat.MP4
            elif extension == 'webm':
                format = VideoFormat.WEBM
            else:
                format = VideoFormat.AVI  # Default fallback
            
            # Parse status
            status_str = file_info.get("status", "unknown")
            try:
                status = VideoStatus(status_str)
            except ValueError:
                status = VideoStatus.UNKNOWN
            
            # Parse timestamps
            start_time = None
            if file_info.get("start_time"):
                start_time = datetime.fromisoformat(file_info["start_time"])
            
            end_time = None
            if file_info.get("end_time"):
                end_time = datetime.fromisoformat(file_info["end_time"])
            
            created_at = start_time or datetime.now()
            
            return VideoFile(
                file_id=file_info["file_id"],
                camera_name=file_info["camera_name"],
                filename=file_info["filename"],
                file_path=file_path,
                file_size_bytes=file_info.get("file_size_bytes", 0),
                created_at=created_at,
                status=status,
                format=format,
                start_time=start_time,
                end_time=end_time,
                machine_trigger=file_info.get("machine_trigger"),
                error_message=None  # Could be added to storage manager later
            )
        
        except Exception as e:
            self.logger.error(f"Error converting file info to VideoFile: {e}")
            raise
