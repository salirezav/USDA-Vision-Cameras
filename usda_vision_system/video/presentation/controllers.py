"""
Video HTTP Controllers.

Handle HTTP requests and responses for video operations.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from ..application.video_service import VideoService
from ..application.streaming_service import StreamingService
from ..domain.models import StreamRange, VideoFile
from .schemas import VideoInfoResponse, VideoListResponse, VideoListRequest, StreamingInfoResponse, ThumbnailRequest, VideoMetadataResponse


class VideoController:
    """Controller for video management operations"""

    def __init__(self, video_service: VideoService):
        self.video_service = video_service
        self.logger = logging.getLogger(__name__)

    async def get_video_info(self, file_id: str) -> VideoInfoResponse:
        """Get video information"""
        video_file = await self.video_service.get_video_by_id(file_id)
        if not video_file:
            raise HTTPException(status_code=404, detail=f"Video {file_id} not found")

        return self._convert_to_response(video_file)

    async def list_videos(self, request: VideoListRequest) -> VideoListResponse:
        """List videos with optional filters"""
        if request.camera_name:
            videos = await self.video_service.get_videos_by_camera(camera_name=request.camera_name, start_date=request.start_date, end_date=request.end_date, limit=request.limit, include_metadata=request.include_metadata)
        else:
            videos = await self.video_service.get_all_videos(start_date=request.start_date, end_date=request.end_date, limit=request.limit, include_metadata=request.include_metadata)

        video_responses = [self._convert_to_response(video) for video in videos]

        return VideoListResponse(videos=video_responses, total_count=len(video_responses))

    async def get_video_thumbnail(self, file_id: str, thumbnail_request: ThumbnailRequest) -> Response:
        """Get video thumbnail"""
        thumbnail_data = await self.video_service.get_video_thumbnail(file_id=file_id, timestamp_seconds=thumbnail_request.timestamp_seconds, size=(thumbnail_request.width, thumbnail_request.height))

        if not thumbnail_data:
            raise HTTPException(status_code=404, detail=f"Could not generate thumbnail for {file_id}")

        return Response(content=thumbnail_data, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=3600", "Content-Length": str(len(thumbnail_data))})  # Cache for 1 hour

    async def validate_video(self, file_id: str) -> dict:
        """Validate video file"""
        is_valid = await self.video_service.validate_video(file_id)
        return {"file_id": file_id, "is_valid": is_valid}

    def _convert_to_response(self, video_file: VideoFile) -> VideoInfoResponse:
        """Convert domain model to response model"""
        metadata_response = None
        if video_file.metadata:
            metadata_response = VideoMetadataResponse(duration_seconds=video_file.metadata.duration_seconds, width=video_file.metadata.width, height=video_file.metadata.height, fps=video_file.metadata.fps, codec=video_file.metadata.codec, bitrate=video_file.metadata.bitrate, aspect_ratio=video_file.metadata.aspect_ratio)

        return VideoInfoResponse(
            file_id=video_file.file_id,
            camera_name=video_file.camera_name,
            filename=video_file.filename,
            file_size_bytes=video_file.file_size_bytes,
            format=video_file.format.value,
            status=video_file.status.value,
            created_at=video_file.created_at,
            start_time=video_file.start_time,
            end_time=video_file.end_time,
            machine_trigger=video_file.machine_trigger,
            metadata=metadata_response,
            is_streamable=video_file.is_streamable,
            needs_conversion=video_file.needs_conversion(),
        )


class StreamingController:
    """Controller for video streaming operations"""

    def __init__(self, streaming_service: StreamingService, video_service: VideoService):
        self.streaming_service = streaming_service
        self.video_service = video_service
        self.logger = logging.getLogger(__name__)

    async def get_streaming_info(self, file_id: str) -> StreamingInfoResponse:
        """Get streaming information for a video"""
        video_file = await self.streaming_service.get_video_info(file_id)
        if not video_file:
            raise HTTPException(status_code=404, detail=f"Video {file_id} not found")

        chunk_size = await self.streaming_service.get_optimal_chunk_size(video_file.file_size_bytes)
        content_type = self._get_content_type(video_file)

        return StreamingInfoResponse(file_id=file_id, file_size_bytes=video_file.file_size_bytes, content_type=content_type, supports_range_requests=True, chunk_size_bytes=chunk_size)

    async def stream_video(self, file_id: str, request: Request) -> Response:
        """Stream video with range request support"""
        # Prepare video for streaming (convert if needed)
        video_file = await self.video_service.prepare_for_streaming(file_id)
        if not video_file:
            raise HTTPException(status_code=404, detail=f"Video {file_id} not found or not streamable")

        # Parse range header
        range_header = request.headers.get("range")
        range_request = None

        if range_header:
            try:
                range_request = StreamRange.from_header(range_header, video_file.file_size_bytes)
            except ValueError as e:
                raise HTTPException(status_code=416, detail=f"Invalid range request: {e}")

        # Determine response type and headers
        content_type = self._get_content_type(video_file)
        headers = {"Accept-Ranges": "bytes", "Cache-Control": "public, max-age=3600"}

        # Handle range requests for progressive streaming
        if range_request:
            # Validate range
            actual_range = self.streaming_service._validate_range(range_request, video_file.file_size_bytes)
            if not actual_range:
                raise HTTPException(status_code=416, detail="Range not satisfiable")

            headers["Content-Range"] = self.streaming_service.calculate_content_range_header(actual_range, video_file.file_size_bytes)
            headers["Content-Length"] = str(actual_range.end - actual_range.start + 1)

            # Create streaming generator for range
            async def generate_range():
                try:
                    import aiofiles

                    async with aiofiles.open(video_file.file_path, "rb") as f:
                        await f.seek(actual_range.start)
                        remaining = actual_range.end - actual_range.start + 1
                        chunk_size = min(8192, remaining)  # 8KB chunks

                        while remaining > 0:
                            chunk_size = min(chunk_size, remaining)
                            chunk = await f.read(chunk_size)
                            if not chunk:
                                break
                            remaining -= len(chunk)
                            yield chunk
                except Exception as e:
                    self.logger.error(f"Error streaming range for {file_id}: {e}")
                    raise

            return StreamingResponse(generate_range(), status_code=206, headers=headers, media_type=content_type)
        else:
            # Stream entire file
            headers["Content-Length"] = str(video_file.file_size_bytes)

            async def generate_full():
                try:
                    import aiofiles

                    async with aiofiles.open(video_file.file_path, "rb") as f:
                        chunk_size = 8192  # 8KB chunks
                        while True:
                            chunk = await f.read(chunk_size)
                            if not chunk:
                                break
                            yield chunk
                except Exception as e:
                    self.logger.error(f"Error streaming full file for {file_id}: {e}")
                    raise

            return StreamingResponse(generate_full(), status_code=200, headers=headers, media_type=content_type)

    async def invalidate_cache(self, file_id: str) -> dict:
        """Invalidate streaming cache for a video"""
        success = await self.streaming_service.invalidate_cache(file_id)
        return {"file_id": file_id, "cache_invalidated": success}

    def _get_content_type(self, video_file: VideoFile) -> str:
        """Get MIME content type for video file"""
        format_to_mime = {"avi": "video/x-msvideo", "mp4": "video/mp4", "webm": "video/webm"}
        return format_to_mime.get(video_file.format.value, "application/octet-stream")
