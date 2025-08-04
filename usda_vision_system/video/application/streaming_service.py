"""
Video Streaming Application Service.

Handles video streaming use cases including range requests and caching.
"""

import asyncio
import logging
from typing import Optional, Tuple

from ..domain.interfaces import VideoRepository, StreamingCache
from ..domain.models import VideoFile, StreamRange


class StreamingService:
    """Application service for video streaming"""
    
    def __init__(
        self,
        video_repository: VideoRepository,
        streaming_cache: Optional[StreamingCache] = None
    ):
        self.video_repository = video_repository
        self.streaming_cache = streaming_cache
        self.logger = logging.getLogger(__name__)
    
    async def stream_video_range(
        self,
        file_id: str,
        range_request: Optional[StreamRange] = None
    ) -> Tuple[Optional[bytes], Optional[VideoFile], Optional[StreamRange]]:
        """
        Stream video data for a specific range.
        
        Returns:
            Tuple of (data, video_file, actual_range)
        """
        try:
            # Get video file
            video_file = await self.video_repository.get_by_id(file_id)
            if not video_file or not video_file.is_streamable:
                return None, None, None
            
            # If no range specified, create range for entire file
            if range_request is None:
                range_request = StreamRange(start=0, end=video_file.file_size_bytes - 1)
            
            # Validate and adjust range
            actual_range = self._validate_range(range_request, video_file.file_size_bytes)
            if not actual_range:
                return None, video_file, None
            
            # Try to get from cache first
            if self.streaming_cache:
                cached_data = await self.streaming_cache.get_cached_range(file_id, actual_range)
                if cached_data:
                    self.logger.debug(f"Serving cached range for {file_id}")
                    return cached_data, video_file, actual_range
            
            # Read from file
            data = await self.video_repository.get_file_range(video_file, actual_range)
            
            # Cache the data if caching is enabled
            if self.streaming_cache and data:
                await self.streaming_cache.cache_range(file_id, actual_range, data)
            
            return data, video_file, actual_range
        
        except Exception as e:
            self.logger.error(f"Error streaming video range for {file_id}: {e}")
            return None, None, None
    
    async def get_video_info(self, file_id: str) -> Optional[VideoFile]:
        """Get video information for streaming"""
        try:
            video_file = await self.video_repository.get_by_id(file_id)
            if not video_file or not video_file.is_streamable:
                return None
            
            return video_file
        
        except Exception as e:
            self.logger.error(f"Error getting video info for {file_id}: {e}")
            return None
    
    async def invalidate_cache(self, file_id: str) -> bool:
        """Invalidate cached data for a video file"""
        try:
            if self.streaming_cache:
                await self.streaming_cache.invalidate_file(file_id)
                self.logger.info(f"Invalidated cache for {file_id}")
                return True
            return False
        
        except Exception as e:
            self.logger.error(f"Error invalidating cache for {file_id}: {e}")
            return False
    
    async def cleanup_cache(self, max_size_mb: int = 100) -> int:
        """Clean up streaming cache"""
        try:
            if self.streaming_cache:
                return await self.streaming_cache.cleanup_cache(max_size_mb)
            return 0
        
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")
            return 0
    
    def _validate_range(self, range_request: StreamRange, file_size: int) -> Optional[StreamRange]:
        """Validate and adjust range request for file size"""
        try:
            start = range_request.start
            end = range_request.end
            
            # Validate start position
            if start < 0:
                start = 0
            elif start >= file_size:
                return None
            
            # Validate end position
            if end is None or end >= file_size:
                end = file_size - 1
            elif end < start:
                return None
            
            return StreamRange(start=start, end=end)
        
        except Exception as e:
            self.logger.error(f"Error validating range: {e}")
            return None
    
    def calculate_content_range_header(
        self,
        range_request: StreamRange,
        file_size: int
    ) -> str:
        """Calculate Content-Range header value"""
        return f"bytes {range_request.start}-{range_request.end}/{file_size}"
    
    def should_use_partial_content(self, range_request: Optional[StreamRange], file_size: int) -> bool:
        """Determine if response should use 206 Partial Content"""
        if not range_request:
            return False
        
        # Use partial content if not requesting the entire file
        return not (range_request.start == 0 and range_request.end == file_size - 1)
    
    async def get_optimal_chunk_size(self, file_size: int) -> int:
        """Get optimal chunk size for streaming based on file size"""
        # Adaptive chunk sizing
        if file_size < 1024 * 1024:  # < 1MB
            return 64 * 1024  # 64KB chunks
        elif file_size < 10 * 1024 * 1024:  # < 10MB
            return 256 * 1024  # 256KB chunks
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            return 512 * 1024  # 512KB chunks
        else:
            return 1024 * 1024  # 1MB chunks for large files
