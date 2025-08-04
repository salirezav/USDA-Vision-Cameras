"""
Video Format Converters.

Implementations for converting video formats using FFmpeg.
"""

import asyncio
import logging
import shutil
from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta

from ..domain.interfaces import VideoConverter
from ..domain.models import VideoFormat


class FFmpegVideoConverter(VideoConverter):
    """FFmpeg-based video converter"""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = temp_dir or Path("/tmp/video_conversions")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if FFmpeg is available
        self._ffmpeg_available = shutil.which("ffmpeg") is not None
        if not self._ffmpeg_available:
            self.logger.warning("FFmpeg not found - video conversion will be disabled")
    
    async def convert(
        self,
        source_path: Path,
        target_path: Path,
        target_format: VideoFormat,
        quality: Optional[str] = None
    ) -> bool:
        """Convert video to target format"""
        if not self._ffmpeg_available:
            self.logger.error("FFmpeg not available for conversion")
            return False
        
        try:
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(source_path, target_path, target_format, quality)
            
            self.logger.info(f"Converting {source_path} to {target_path} using FFmpeg")
            
            # Run FFmpeg conversion
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(f"Successfully converted {source_path} to {target_path}")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
                self.logger.error(f"FFmpeg conversion failed: {error_msg}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error during video conversion: {e}")
            return False
    
    async def is_conversion_needed(
        self,
        source_format: VideoFormat,
        target_format: VideoFormat
    ) -> bool:
        """Check if conversion is needed"""
        return source_format != target_format
    
    async def get_converted_path(
        self,
        original_path: Path,
        target_format: VideoFormat
    ) -> Path:
        """Get path for converted file"""
        # Place converted files in temp directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = original_path.stem
        converted_filename = f"{stem}_{timestamp}.{target_format.value}"
        return self.temp_dir / converted_filename
    
    async def cleanup_converted_files(self, max_age_hours: int = 24) -> int:
        """Clean up old converted files"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            files_removed = 0
            
            if not self.temp_dir.exists():
                return 0
            
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    # Get file modification time
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            files_removed += 1
                            self.logger.debug(f"Removed old converted file: {file_path}")
                        except Exception as e:
                            self.logger.warning(f"Could not remove {file_path}: {e}")
            
            self.logger.info(f"Cleaned up {files_removed} old converted files")
            return files_removed
        
        except Exception as e:
            self.logger.error(f"Error during converted files cleanup: {e}")
            return 0
    
    def _build_ffmpeg_command(
        self,
        source_path: Path,
        target_path: Path,
        target_format: VideoFormat,
        quality: Optional[str] = None
    ) -> list:
        """Build FFmpeg command for conversion"""
        cmd = ["ffmpeg", "-i", str(source_path)]
        
        # Add format-specific options
        if target_format == VideoFormat.MP4:
            cmd.extend([
                "-c:v", "libx264",  # H.264 video codec
                "-c:a", "aac",      # AAC audio codec
                "-movflags", "+faststart",  # Enable progressive download
            ])
            
            # Quality settings
            if quality == "high":
                cmd.extend(["-crf", "18"])
            elif quality == "medium":
                cmd.extend(["-crf", "23"])
            elif quality == "low":
                cmd.extend(["-crf", "28"])
            else:
                cmd.extend(["-crf", "23"])  # Default medium quality
        
        elif target_format == VideoFormat.WEBM:
            cmd.extend([
                "-c:v", "libvpx-vp9",  # VP9 video codec
                "-c:a", "libopus",     # Opus audio codec
            ])
            
            # Quality settings for WebM
            if quality == "high":
                cmd.extend(["-crf", "15", "-b:v", "0"])
            elif quality == "medium":
                cmd.extend(["-crf", "20", "-b:v", "0"])
            elif quality == "low":
                cmd.extend(["-crf", "25", "-b:v", "0"])
            else:
                cmd.extend(["-crf", "20", "-b:v", "0"])  # Default medium quality
        
        # Common options
        cmd.extend([
            "-preset", "fast",      # Encoding speed vs compression trade-off
            "-y",                   # Overwrite output file
            str(target_path)
        ])
        
        return cmd


class NoOpVideoConverter(VideoConverter):
    """No-operation converter for when FFmpeg is not available"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def convert(
        self,
        source_path: Path,
        target_path: Path,
        target_format: VideoFormat,
        quality: Optional[str] = None
    ) -> bool:
        """No-op conversion - just copy file if formats match"""
        try:
            if source_path.suffix.lower().lstrip('.') == target_format.value:
                # Same format, just copy
                shutil.copy2(source_path, target_path)
                return True
            else:
                self.logger.warning(f"Cannot convert {source_path} to {target_format} - no converter available")
                return False
        except Exception as e:
            self.logger.error(f"Error in no-op conversion: {e}")
            return False
    
    async def is_conversion_needed(
        self,
        source_format: VideoFormat,
        target_format: VideoFormat
    ) -> bool:
        """Check if conversion is needed"""
        return source_format != target_format
    
    async def get_converted_path(
        self,
        original_path: Path,
        target_format: VideoFormat
    ) -> Path:
        """Get path for converted file"""
        return original_path.with_suffix(f".{target_format.value}")
    
    async def cleanup_converted_files(self, max_age_hours: int = 24) -> int:
        """No-op cleanup"""
        return 0
