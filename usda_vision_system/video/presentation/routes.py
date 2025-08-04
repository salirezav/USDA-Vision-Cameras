"""
Video API Routes.

FastAPI route definitions for video streaming and management.
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from .controllers import VideoController, StreamingController
from .schemas import (
    VideoInfoResponse, VideoListResponse, VideoListRequest,
    StreamingInfoResponse, ThumbnailRequest
)


def create_video_routes(
    video_controller: VideoController,
    streaming_controller: StreamingController
) -> APIRouter:
    """Create video API routes with dependency injection"""
    
    router = APIRouter(prefix="/videos", tags=["videos"])
    
    @router.get("/", response_model=VideoListResponse)
    async def list_videos(
        camera_name: Optional[str] = Query(None, description="Filter by camera name"),
        start_date: Optional[datetime] = Query(None, description="Filter by start date"),
        end_date: Optional[datetime] = Query(None, description="Filter by end date"),
        limit: Optional[int] = Query(50, description="Maximum number of results"),
        include_metadata: bool = Query(False, description="Include video metadata")
    ):
        """
        List videos with optional filters.
        
        - **camera_name**: Filter videos by camera name
        - **start_date**: Filter videos created after this date
        - **end_date**: Filter videos created before this date  
        - **limit**: Maximum number of videos to return
        - **include_metadata**: Whether to include video metadata (duration, resolution, etc.)
        """
        request = VideoListRequest(
            camera_name=camera_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            include_metadata=include_metadata
        )
        return await video_controller.list_videos(request)
    
    @router.get("/{file_id}", response_model=VideoInfoResponse)
    async def get_video_info(file_id: str):
        """
        Get detailed information about a specific video.
        
        - **file_id**: Unique identifier for the video file
        """
        return await video_controller.get_video_info(file_id)
    
    @router.get("/{file_id}/stream")
    async def stream_video(file_id: str, request: Request):
        """
        Stream video with HTTP range request support.
        
        Supports:
        - **Range requests**: For seeking and progressive download
        - **Partial content**: 206 responses for range requests
        - **Format conversion**: Automatic conversion to web-compatible formats
        - **Caching**: Intelligent caching for better performance
        
        Usage in HTML5:
        ```html
        <video controls>
            <source src="/videos/{file_id}/stream" type="video/mp4">
        </video>
        ```
        """
        return await streaming_controller.stream_video(file_id, request)
    
    @router.get("/{file_id}/info", response_model=StreamingInfoResponse)
    async def get_streaming_info(file_id: str):
        """
        Get streaming information for a video.
        
        Returns technical details needed for optimal streaming:
        - File size and content type
        - Range request support
        - Recommended chunk size
        """
        return await streaming_controller.get_streaming_info(file_id)
    
    @router.get("/{file_id}/thumbnail")
    async def get_video_thumbnail(
        file_id: str,
        timestamp: float = Query(1.0, description="Timestamp in seconds to extract thumbnail from"),
        width: int = Query(320, description="Thumbnail width in pixels"),
        height: int = Query(240, description="Thumbnail height in pixels")
    ):
        """
        Generate and return a thumbnail image from the video.
        
        - **file_id**: Video file identifier
        - **timestamp**: Time position in seconds to extract thumbnail from
        - **width**: Thumbnail width in pixels
        - **height**: Thumbnail height in pixels
        
        Returns JPEG image data.
        """
        thumbnail_request = ThumbnailRequest(
            timestamp_seconds=timestamp,
            width=width,
            height=height
        )
        return await video_controller.get_video_thumbnail(file_id, thumbnail_request)
    
    @router.post("/{file_id}/validate")
    async def validate_video(file_id: str):
        """
        Validate that a video file is accessible and playable.
        
        - **file_id**: Video file identifier
        
        Returns validation status and any issues found.
        """
        return await video_controller.validate_video(file_id)
    
    @router.post("/{file_id}/cache/invalidate")
    async def invalidate_video_cache(file_id: str):
        """
        Invalidate cached data for a video file.
        
        Useful when a video file has been updated or replaced.
        
        - **file_id**: Video file identifier
        """
        return await streaming_controller.invalidate_cache(file_id)
    
    return router


def create_admin_video_routes(streaming_controller: StreamingController) -> APIRouter:
    """Create admin routes for video management"""
    
    router = APIRouter(prefix="/admin/videos", tags=["admin", "videos"])
    
    @router.post("/cache/cleanup")
    async def cleanup_video_cache(
        max_size_mb: int = Query(100, description="Maximum cache size in MB")
    ):
        """
        Clean up video streaming cache.
        
        Removes old cached data to keep cache size under the specified limit.
        
        - **max_size_mb**: Maximum cache size to maintain
        """
        entries_removed = await streaming_controller.streaming_service.cleanup_cache(max_size_mb)
        return {
            "cache_cleaned": True,
            "entries_removed": entries_removed,
            "max_size_mb": max_size_mb
        }
    
    return router
