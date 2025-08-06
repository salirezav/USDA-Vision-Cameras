"""
Configuration management for the USDA Vision Camera System.

This module handles all configuration settings including MQTT broker settings,
camera configurations, storage paths, and system parameters.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class MQTTConfig:
    """MQTT broker configuration"""

    broker_host: str = "192.168.1.110"
    broker_port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    topics: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.topics is None:
            self.topics = {"vibratory_conveyor": "vision/vibratory_conveyor/state", "blower_separator": "vision/blower_separator/state"}


@dataclass
class CameraConfig:
    """Individual camera configuration"""

    name: str
    machine_topic: str  # Which MQTT topic triggers this camera
    storage_path: str
    exposure_ms: float = 1.0
    gain: float = 3.5
    target_fps: float = 3.0
    enabled: bool = True

    # Video recording settings
    video_format: str = "mp4"  # Video file format (mp4, avi)
    video_codec: str = "mp4v"  # Video codec (mp4v for MP4, XVID for AVI)
    video_quality: int = 95  # Video quality (0-100, higher is better)

    # Auto-recording settings
    auto_start_recording_enabled: bool = False  # Enable automatic recording when machine turns on
    auto_recording_max_retries: int = 3  # Maximum retry attempts for failed auto-recording starts
    auto_recording_retry_delay_seconds: int = 5  # Delay between retry attempts

    # Image Quality Settings
    sharpness: int = 100  # 0-200, default 100 (no sharpening)
    contrast: int = 100  # 0-200, default 100 (normal contrast)
    saturation: int = 100  # 0-200, default 100 (normal saturation, color cameras only)
    gamma: int = 100  # 0-300, default 100 (normal gamma)

    # Noise Reduction
    noise_filter_enabled: bool = True  # Enable basic noise filtering
    denoise_3d_enabled: bool = False  # Enable advanced 3D denoising (may reduce FPS)

    # Color Settings (for color cameras)
    auto_white_balance: bool = True  # Enable automatic white balance
    color_temperature_preset: int = 0  # 0=auto, 1=daylight, 2=fluorescent, etc.

    # Manual White Balance RGB Gains (for manual white balance mode)
    wb_red_gain: float = 1.0  # Red channel gain (0.0-3.99, default 1.0)
    wb_green_gain: float = 1.0  # Green channel gain (0.0-3.99, default 1.0)
    wb_blue_gain: float = 1.0  # Blue channel gain (0.0-3.99, default 1.0)

    # Advanced Settings
    anti_flicker_enabled: bool = True  # Reduce artificial lighting flicker
    light_frequency: int = 1  # 0=50Hz, 1=60Hz (match local power frequency)

    # Bit Depth & Format
    bit_depth: int = 8  # 8, 10, 12, or 16 bits per channel

    # HDR Settings
    hdr_enabled: bool = False  # Enable High Dynamic Range
    hdr_gain_mode: int = 0  # HDR processing mode


@dataclass
class StorageConfig:
    """Storage configuration"""

    base_path: str = "/storage"
    max_file_size_mb: int = 1000  # Max size per video file
    max_recording_duration_minutes: int = 60  # Max recording duration
    cleanup_older_than_days: int = 30  # Auto cleanup old files


@dataclass
class SystemConfig:
    """System-wide configuration"""

    camera_check_interval_seconds: int = 2
    log_level: str = "INFO"
    log_file: str = "usda_vision_system.log"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    enable_api: bool = True
    timezone: str = "America/New_York"

    # Auto-recording system settings
    auto_recording_enabled: bool = True  # Global enable/disable for auto-recording feature  # Atlanta, Georgia timezone


class Config:
    """Main configuration manager"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config.json"
        self.logger = logging.getLogger(__name__)

        # Default configurations
        self.mqtt = MQTTConfig()
        self.storage = StorageConfig()
        self.system = SystemConfig()

        # Camera configurations - will be populated from config file or defaults
        self.cameras: List[CameraConfig] = []

        # Load configuration
        self.load_config()

        # Ensure storage directories exist
        self._ensure_storage_directories()

    def load_config(self) -> None:
        """Load configuration from file"""
        config_path = Path(self.config_file)

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config_data = json.load(f)

                # Load MQTT config
                if "mqtt" in config_data:
                    mqtt_data = config_data["mqtt"]
                    self.mqtt = MQTTConfig(**mqtt_data)

                # Load storage config
                if "storage" in config_data:
                    storage_data = config_data["storage"]
                    self.storage = StorageConfig(**storage_data)

                # Load system config
                if "system" in config_data:
                    system_data = config_data["system"]
                    self.system = SystemConfig(**system_data)

                # Load camera configs
                if "cameras" in config_data:
                    self.cameras = []
                    for cam_data in config_data["cameras"]:
                        # Set defaults for new video format fields if not present
                        cam_data.setdefault("video_format", "mp4")
                        cam_data.setdefault("video_codec", "mp4v")
                        cam_data.setdefault("video_quality", 95)
                        self.cameras.append(CameraConfig(**cam_data))
                else:
                    self._create_default_camera_configs()

                self.logger.info(f"Configuration loaded from {config_path}")

            except Exception as e:
                self.logger.error(f"Error loading config from {config_path}: {e}")
                self._create_default_camera_configs()
        else:
            self.logger.info(f"Config file {config_path} not found, using defaults")
            self._create_default_camera_configs()
            self.save_config()  # Save default config

    def _create_default_camera_configs(self) -> None:
        """Create default camera configurations"""
        self.cameras = [CameraConfig(name="camera1", machine_topic="vibratory_conveyor", storage_path=os.path.join(self.storage.base_path, "camera1")), CameraConfig(name="camera2", machine_topic="blower_separator", storage_path=os.path.join(self.storage.base_path, "camera2"))]

    def save_config(self) -> None:
        """Save current configuration to file"""
        config_data = {"mqtt": asdict(self.mqtt), "storage": asdict(self.storage), "system": asdict(self.system), "cameras": [asdict(cam) for cam in self.cameras]}

        try:
            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Error saving config to {self.config_file}: {e}")

    def _ensure_storage_directories(self) -> None:
        """Ensure all storage directories exist"""
        try:
            # Create base storage directory
            Path(self.storage.base_path).mkdir(parents=True, exist_ok=True)

            # Create camera-specific directories
            for camera in self.cameras:
                Path(camera.storage_path).mkdir(parents=True, exist_ok=True)

            self.logger.info("Storage directories verified/created")
        except Exception as e:
            self.logger.error(f"Error creating storage directories: {e}")

    def get_camera_by_topic(self, topic: str) -> Optional[CameraConfig]:
        """Get camera configuration by MQTT topic"""
        for camera in self.cameras:
            if camera.machine_topic == topic:
                return camera
        return None

    def get_camera_by_name(self, name: str) -> Optional[CameraConfig]:
        """Get camera configuration by name"""
        for camera in self.cameras:
            if camera.name == name:
                return camera
        return None

    def update_camera_config(self, name: str, **kwargs) -> bool:
        """Update camera configuration"""
        camera = self.get_camera_by_name(name)
        if camera:
            for key, value in kwargs.items():
                if hasattr(camera, key):
                    setattr(camera, key, value)
            self.save_config()
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {"mqtt": asdict(self.mqtt), "storage": asdict(self.storage), "system": asdict(self.system), "cameras": [asdict(cam) for cam in self.cameras]}
