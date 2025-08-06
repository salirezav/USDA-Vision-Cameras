"""
Video Metadata Extractors.

Implementations for extracting video metadata using OpenCV and other tools.
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path
import cv2
import numpy as np

from ..domain.interfaces import MetadataExtractor
from ..domain.models import VideoMetadata


class OpenCVMetadataExtractor(MetadataExtractor):
    """OpenCV-based metadata extractor"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract(self, file_path: Path) -> Optional[VideoMetadata]:
        """Extract metadata from video file using OpenCV"""
        try:
            # Run OpenCV operations in thread pool to avoid blocking
            return await asyncio.get_event_loop().run_in_executor(
                None, self._extract_sync, file_path
            )
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {file_path}: {e}")
            return None
    
    def _extract_sync(self, file_path: Path) -> Optional[VideoMetadata]:
        """Synchronous metadata extraction"""
        cap = None
        try:
            cap = cv2.VideoCapture(str(file_path))
            
            if not cap.isOpened():
                self.logger.warning(f"Could not open video file: {file_path}")
                return None
            
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate duration
            duration_seconds = frame_count / fps if fps > 0 else 0.0
            
            # Get codec information
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = self._fourcc_to_string(fourcc)
            
            # Try to get bitrate (not always available)
            bitrate = cap.get(cv2.CAP_PROP_BITRATE)
            bitrate = int(bitrate) if bitrate > 0 else None
            
            return VideoMetadata(
                duration_seconds=duration_seconds,
                width=width,
                height=height,
                fps=fps,
                codec=codec,
                bitrate=bitrate
            )
        
        except Exception as e:
            self.logger.error(f"Error in sync metadata extraction: {e}")
            return None
        
        finally:
            if cap is not None:
                cap.release()
    
    async def extract_thumbnail(
        self,
        file_path: Path,
        timestamp_seconds: float = 1.0,
        size: tuple = (320, 240)
    ) -> Optional[bytes]:
        """Extract thumbnail image from video"""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._extract_thumbnail_sync, file_path, timestamp_seconds, size
            )
        except Exception as e:
            self.logger.error(f"Error extracting thumbnail from {file_path}: {e}")
            return None
    
    def _extract_thumbnail_sync(
        self,
        file_path: Path,
        timestamp_seconds: float,
        size: tuple
    ) -> Optional[bytes]:
        """Synchronous thumbnail extraction"""
        cap = None
        try:
            cap = cv2.VideoCapture(str(file_path))
            
            if not cap.isOpened():
                return None
            
            # Get video FPS to calculate frame number
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # Default fallback
            
            # Calculate target frame
            target_frame = int(timestamp_seconds * fps)
            
            # Set position to target frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
            # Read frame
            ret, frame = cap.read()
            if not ret or frame is None:
                # Fallback to first frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret or frame is None:
                    return None
            
            # Resize frame to thumbnail size
            thumbnail = cv2.resize(frame, size)
            
            # Encode as JPEG
            success, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if success:
                return buffer.tobytes()
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error in sync thumbnail extraction: {e}")
            return None
        
        finally:
            if cap is not None:
                cap.release()
    
    async def is_valid_video(self, file_path: Path) -> bool:
        """Check if file is a valid video"""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._is_valid_video_sync, file_path
            )
        except Exception as e:
            self.logger.error(f"Error validating video {file_path}: {e}")
            return False
    
    def _is_valid_video_sync(self, file_path: Path) -> bool:
        """Synchronous video validation"""
        cap = None
        try:
            if not file_path.exists():
                return False
            
            cap = cv2.VideoCapture(str(file_path))
            
            if not cap.isOpened():
                return False
            
            # Try to read first frame
            ret, frame = cap.read()
            return ret and frame is not None
        
        except Exception:
            return False
        
        finally:
            if cap is not None:
                cap.release()
    
    def _fourcc_to_string(self, fourcc: int) -> str:
        """Convert OpenCV fourcc code to string"""
        try:
            # Convert fourcc integer to 4-character string
            fourcc_bytes = [
                (fourcc & 0xFF),
                ((fourcc >> 8) & 0xFF),
                ((fourcc >> 16) & 0xFF),
                ((fourcc >> 24) & 0xFF)
            ]
            
            # Convert to string, handling non-printable characters
            codec_chars = []
            for byte_val in fourcc_bytes:
                if 32 <= byte_val <= 126:  # Printable ASCII
                    codec_chars.append(chr(byte_val))
                else:
                    codec_chars.append('?')
            
            return ''.join(codec_chars).strip()
        
        except Exception:
            return "UNKNOWN"
