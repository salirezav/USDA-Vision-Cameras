"""
Video Module Integration.

Integrates the modular video system with the existing USDA Vision Camera System.
This module handles dependency injection and service composition.
"""

import logging
from typing import Optional

from ..core.config import Config
from ..storage.manager import StorageManager

# Domain interfaces
from .domain.interfaces import VideoRepository, VideoConverter, MetadataExtractor, StreamingCache

# Infrastructure implementations
from .infrastructure.repositories import FileSystemVideoRepository
from .infrastructure.converters import FFmpegVideoConverter, NoOpVideoConverter
from .infrastructure.metadata_extractors import OpenCVMetadataExtractor
from .infrastructure.caching import InMemoryStreamingCache, NoOpStreamingCache

# Application services
from .application.video_service import VideoService
from .application.streaming_service import StreamingService

# Presentation layer
from .presentation.controllers import VideoController, StreamingController
from .presentation.routes import create_video_routes, create_admin_video_routes


class VideoModuleConfig:
    """Configuration for video module"""
    
    def __init__(
        self,
        enable_caching: bool = True,
        cache_size_mb: int = 100,
        cache_max_age_minutes: int = 30,
        enable_conversion: bool = True,
        conversion_quality: str = "medium"
    ):
        self.enable_caching = enable_caching
        self.cache_size_mb = cache_size_mb
        self.cache_max_age_minutes = cache_max_age_minutes
        self.enable_conversion = enable_conversion
        self.conversion_quality = conversion_quality


class VideoModule:
    """
    Main video module that provides dependency injection and service composition.
    
    This class follows the composition root pattern, creating and wiring up
    all dependencies for the video streaming functionality.
    """
    
    def __init__(
        self,
        config: Config,
        storage_manager: StorageManager,
        video_config: Optional[VideoModuleConfig] = None
    ):
        self.config = config
        self.storage_manager = storage_manager
        self.video_config = video_config or VideoModuleConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self._initialize_services()
        
        self.logger.info("Video module initialized successfully")
    
    def _initialize_services(self):
        """Initialize all video services with proper dependency injection"""
        
        # Infrastructure layer
        self.video_repository = self._create_video_repository()
        self.video_converter = self._create_video_converter()
        self.metadata_extractor = self._create_metadata_extractor()
        self.streaming_cache = self._create_streaming_cache()
        
        # Application layer
        self.video_service = VideoService(
            video_repository=self.video_repository,
            metadata_extractor=self.metadata_extractor,
            video_converter=self.video_converter
        )
        
        self.streaming_service = StreamingService(
            video_repository=self.video_repository,
            streaming_cache=self.streaming_cache
        )
        
        # Presentation layer
        self.video_controller = VideoController(self.video_service)
        self.streaming_controller = StreamingController(
            streaming_service=self.streaming_service,
            video_service=self.video_service
        )
    
    def _create_video_repository(self) -> VideoRepository:
        """Create video repository implementation"""
        return FileSystemVideoRepository(
            config=self.config,
            storage_manager=self.storage_manager
        )
    
    def _create_video_converter(self) -> VideoConverter:
        """Create video converter implementation"""
        if self.video_config.enable_conversion:
            try:
                return FFmpegVideoConverter()
            except Exception as e:
                self.logger.warning(f"FFmpeg converter not available, using no-op converter: {e}")
                return NoOpVideoConverter()
        else:
            return NoOpVideoConverter()
    
    def _create_metadata_extractor(self) -> MetadataExtractor:
        """Create metadata extractor implementation"""
        return OpenCVMetadataExtractor()
    
    def _create_streaming_cache(self) -> StreamingCache:
        """Create streaming cache implementation"""
        if self.video_config.enable_caching:
            return InMemoryStreamingCache(
                max_size_mb=self.video_config.cache_size_mb,
                max_age_minutes=self.video_config.cache_max_age_minutes
            )
        else:
            return NoOpStreamingCache()
    
    def get_api_routes(self):
        """Get FastAPI routes for video functionality"""
        return create_video_routes(
            video_controller=self.video_controller,
            streaming_controller=self.streaming_controller
        )
    
    def get_admin_routes(self):
        """Get admin routes for video management"""
        return create_admin_video_routes(
            streaming_controller=self.streaming_controller
        )
    
    async def cleanup(self):
        """Clean up video module resources"""
        try:
            # Clean up cache
            if self.streaming_cache:
                await self.streaming_cache.cleanup_cache()
            
            # Clean up converted files
            if self.video_converter:
                await self.video_converter.cleanup_converted_files()
            
            self.logger.info("Video module cleanup completed")
        
        except Exception as e:
            self.logger.error(f"Error during video module cleanup: {e}")
    
    def get_module_status(self) -> dict:
        """Get status information about the video module"""
        return {
            "video_repository": type(self.video_repository).__name__,
            "video_converter": type(self.video_converter).__name__,
            "metadata_extractor": type(self.metadata_extractor).__name__,
            "streaming_cache": type(self.streaming_cache).__name__,
            "caching_enabled": self.video_config.enable_caching,
            "conversion_enabled": self.video_config.enable_conversion,
            "cache_size_mb": self.video_config.cache_size_mb
        }


def create_video_module(
    config: Config,
    storage_manager: StorageManager,
    enable_caching: bool = True,
    enable_conversion: bool = True
) -> VideoModule:
    """
    Factory function to create a configured video module.
    
    This is the main entry point for integrating video functionality
    into the existing USDA Vision Camera System.
    """
    video_config = VideoModuleConfig(
        enable_caching=enable_caching,
        enable_conversion=enable_conversion
    )
    
    return VideoModule(
        config=config,
        storage_manager=storage_manager,
        video_config=video_config
    )
