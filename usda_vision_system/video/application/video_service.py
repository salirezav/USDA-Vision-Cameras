"""
Video Application Service.

Orchestrates video-related use cases and business logic.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from ..domain.interfaces import VideoRepository, MetadataExtractor, VideoConverter
from ..domain.models import VideoFile, VideoMetadata, VideoFormat


class VideoService:
    """Application service for video management"""
    
    def __init__(
        self,
        video_repository: VideoRepository,
        metadata_extractor: MetadataExtractor,
        video_converter: VideoConverter
    ):
        self.video_repository = video_repository
        self.metadata_extractor = metadata_extractor
        self.video_converter = video_converter
        self.logger = logging.getLogger(__name__)
    
    async def get_video_by_id(self, file_id: str) -> Optional[VideoFile]:
        """Get video file by ID with metadata"""
        try:
            video_file = await self.video_repository.get_by_id(file_id)
            if not video_file:
                return None
            
            # Ensure metadata is available
            if not video_file.metadata:
                await self._ensure_metadata(video_file)
            
            return video_file
        
        except Exception as e:
            self.logger.error(f"Error getting video {file_id}: {e}")
            return None
    
    async def get_videos_by_camera(
        self,
        camera_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        include_metadata: bool = False
    ) -> List[VideoFile]:
        """Get videos for a camera with optional metadata"""
        try:
            videos = await self.video_repository.get_by_camera(
                camera_name=camera_name,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            if include_metadata:
                # Extract metadata for videos that don't have it
                await self._ensure_metadata_for_videos(videos)
            
            return videos
        
        except Exception as e:
            self.logger.error(f"Error getting videos for camera {camera_name}: {e}")
            return []
    
    async def get_all_videos(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        include_metadata: bool = False
    ) -> List[VideoFile]:
        """Get all videos with optional metadata"""
        try:
            videos = await self.video_repository.get_all(
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            if include_metadata:
                await self._ensure_metadata_for_videos(videos)
            
            return videos
        
        except Exception as e:
            self.logger.error(f"Error getting all videos: {e}")
            return []
    
    async def get_video_thumbnail(
        self,
        file_id: str,
        timestamp_seconds: float = 1.0,
        size: tuple = (320, 240)
    ) -> Optional[bytes]:
        """Get thumbnail for video"""
        try:
            video_file = await self.video_repository.get_by_id(file_id)
            if not video_file or not video_file.is_streamable:
                return None
            
            return await self.metadata_extractor.extract_thumbnail(
                video_file.file_path,
                timestamp_seconds=timestamp_seconds,
                size=size
            )
        
        except Exception as e:
            self.logger.error(f"Error getting thumbnail for {file_id}: {e}")
            return None
    
    async def prepare_for_streaming(self, file_id: str) -> Optional[VideoFile]:
        """Prepare video for web streaming (convert if needed)"""
        try:
            video_file = await self.video_repository.get_by_id(file_id)
            if not video_file:
                return None
            
            # Ensure metadata is available
            await self._ensure_metadata(video_file)
            
            # Check if conversion is needed for web compatibility
            if video_file.needs_conversion():
                converted_file = await self._convert_for_web(video_file)
                return converted_file if converted_file else video_file
            
            return video_file
        
        except Exception as e:
            self.logger.error(f"Error preparing video {file_id} for streaming: {e}")
            return None
    
    async def validate_video(self, file_id: str) -> bool:
        """Validate that video file is accessible and valid"""
        try:
            video_file = await self.video_repository.get_by_id(file_id)
            if not video_file:
                return False
            
            # Check file exists and is readable
            if not video_file.file_path.exists():
                return False
            
            # Validate video format
            return await self.metadata_extractor.is_valid_video(video_file.file_path)
        
        except Exception as e:
            self.logger.error(f"Error validating video {file_id}: {e}")
            return False
    
    async def _ensure_metadata(self, video_file: VideoFile) -> None:
        """Ensure video has metadata extracted"""
        if video_file.metadata:
            return
        
        try:
            metadata = await self.metadata_extractor.extract(video_file.file_path)
            if metadata:
                # Update video file with metadata
                # Note: In a real implementation, you might want to persist this
                video_file.metadata = metadata
                self.logger.debug(f"Extracted metadata for {video_file.file_id}")
        
        except Exception as e:
            self.logger.warning(f"Could not extract metadata for {video_file.file_id}: {e}")
    
    async def _ensure_metadata_for_videos(self, videos: List[VideoFile]) -> None:
        """Extract metadata for multiple videos concurrently"""
        tasks = []
        for video in videos:
            if not video.metadata:
                tasks.append(self._ensure_metadata(video))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _convert_for_web(self, video_file: VideoFile) -> Optional[VideoFile]:
        """Convert video to web-compatible format"""
        try:
            target_format = video_file.web_compatible_format
            
            # Get path for converted file
            converted_path = await self.video_converter.get_converted_path(
                video_file.file_path,
                target_format
            )
            
            # Perform conversion
            success = await self.video_converter.convert(
                source_path=video_file.file_path,
                target_path=converted_path,
                target_format=target_format,
                quality="medium"
            )
            
            if success and converted_path.exists():
                # Create new VideoFile object for converted file
                converted_video = VideoFile(
                    file_id=f"{video_file.file_id}_converted",
                    camera_name=video_file.camera_name,
                    filename=converted_path.name,
                    file_path=converted_path,
                    file_size_bytes=converted_path.stat().st_size,
                    created_at=video_file.created_at,
                    status=video_file.status,
                    format=target_format,
                    metadata=video_file.metadata,
                    start_time=video_file.start_time,
                    end_time=video_file.end_time,
                    machine_trigger=video_file.machine_trigger
                )
                
                self.logger.info(f"Successfully converted {video_file.file_id} to {target_format.value}")
                return converted_video
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error converting video {video_file.file_id}: {e}")
            return None
