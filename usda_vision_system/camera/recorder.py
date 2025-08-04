"""
Camera Recorder for the USDA Vision Camera System.

This module handles video recording from GigE cameras using the camera SDK library (mvsdk).
"""

import sys
import os
import threading
import time
import logging
import cv2
import numpy as np
import contextlib
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

# Add camera SDK to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "camera_sdk"))
import mvsdk

from ..core.config import CameraConfig
from ..core.state_manager import StateManager
from ..core.events import EventSystem, publish_recording_started, publish_recording_stopped, publish_recording_error
from ..core.timezone_utils import now_atlanta, format_filename_timestamp
from .sdk_config import ensure_sdk_initialized


@contextlib.contextmanager
def suppress_camera_errors():
    """Context manager to temporarily suppress camera SDK error output"""
    # Save original file descriptors
    original_stderr = os.dup(2)
    original_stdout = os.dup(1)

    try:
        # Redirect stderr and stdout to devnull
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)  # stderr
        os.dup2(devnull, 1)  # stdout (in case SDK uses stdout)
        os.close(devnull)

        yield

    finally:
        # Restore original file descriptors
        os.dup2(original_stderr, 2)
        os.dup2(original_stdout, 1)
        os.close(original_stderr)
        os.close(original_stdout)


class CameraRecorder:
    """Handles video recording for a single camera"""

    def __init__(self, camera_config: CameraConfig, device_info: Any, state_manager: StateManager, event_system: EventSystem, storage_manager=None):
        self.camera_config = camera_config
        self.device_info = device_info
        self.state_manager = state_manager
        self.event_system = event_system
        self.storage_manager = storage_manager
        self.logger = logging.getLogger(f"{__name__}.{camera_config.name}")

        # Camera handle and properties
        self.hCamera: Optional[int] = None
        self.cap = None
        self.monoCamera = False
        self.frame_buffer = None
        self.frame_buffer_size = 0

        # Recording state
        self.recording = False
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.output_filename: Optional[str] = None
        self.frame_count = 0
        self.start_time: Optional[datetime] = None

        # Threading
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_recording_event = threading.Event()
        self._lock = threading.RLock()

        # Don't initialize camera immediately - use lazy initialization
        # Camera will be initialized when recording starts
        self.logger.info(f"Camera recorder created for: {self.camera_config.name} (lazy initialization)")

    def _initialize_camera(self) -> bool:
        """Initialize the camera with configured settings"""
        try:
            self.logger.info(f"Initializing camera: {self.camera_config.name}")

            # Ensure SDK is initialized
            ensure_sdk_initialized()

            # Check if device_info is valid
            if self.device_info is None:
                self.logger.error("No device info provided for camera initialization")
                return False

            # Initialize camera (suppress output to avoid MVCAMAPI error messages)
            with suppress_camera_errors():
                self.hCamera = mvsdk.CameraInit(self.device_info, -1, -1)
            self.logger.info("Camera initialized successfully")

            # Get camera capabilities
            self.cap = mvsdk.CameraGetCapability(self.hCamera)
            self.monoCamera = self.cap.sIspCapacity.bMonoSensor != 0
            self.logger.info(f"Camera type: {'Monochrome' if self.monoCamera else 'Color'}")

            # Set output format based on bit depth configuration
            if self.monoCamera:
                if self.camera_config.bit_depth == 16:
                    mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO16)
                elif self.camera_config.bit_depth == 12:
                    mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO12)
                elif self.camera_config.bit_depth == 10:
                    mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO10)
                else:  # Default to 8-bit
                    mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
            else:
                if self.camera_config.bit_depth == 16:
                    mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_RGB16)
                elif self.camera_config.bit_depth == 12:
                    mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR12)
                elif self.camera_config.bit_depth == 10:
                    mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR10)
                else:  # Default to 8-bit
                    mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

            self.logger.info(f"Output format set to {self.camera_config.bit_depth}-bit {'mono' if self.monoCamera else 'color'}")

            # Configure camera settings
            self._configure_camera_settings()

            # Allocate frame buffer based on bit depth
            bytes_per_pixel = self._get_bytes_per_pixel()
            self.frame_buffer_size = self.cap.sResolutionRange.iWidthMax * self.cap.sResolutionRange.iHeightMax * bytes_per_pixel
            self.frame_buffer = mvsdk.CameraAlignMalloc(self.frame_buffer_size, 16)

            # Start camera
            mvsdk.CameraPlay(self.hCamera)
            self.logger.info("Camera started successfully")

            return True

        except mvsdk.CameraException as e:
            error_msg = f"Camera initialization failed({e.error_code}): {e.message}"
            if e.error_code == 32774:
                error_msg += " - This may indicate the camera is already in use by another process or there's a resource conflict"
            self.logger.error(error_msg)
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during camera initialization: {e}")
            return False

    def _get_bytes_per_pixel(self) -> int:
        """Calculate bytes per pixel based on camera type and bit depth"""
        if self.monoCamera:
            # Monochrome camera
            if self.camera_config.bit_depth >= 16:
                return 2  # 16-bit mono
            elif self.camera_config.bit_depth >= 12:
                return 2  # 12-bit mono (stored in 16-bit)
            elif self.camera_config.bit_depth >= 10:
                return 2  # 10-bit mono (stored in 16-bit)
            else:
                return 1  # 8-bit mono
        else:
            # Color camera
            if self.camera_config.bit_depth >= 16:
                return 6  # 16-bit RGB (2 bytes × 3 channels)
            elif self.camera_config.bit_depth >= 12:
                return 6  # 12-bit RGB (stored as 16-bit)
            elif self.camera_config.bit_depth >= 10:
                return 6  # 10-bit RGB (stored as 16-bit)
            else:
                return 3  # 8-bit RGB

    def _configure_camera_settings(self) -> None:
        """Configure camera settings from config"""
        try:
            # Set trigger mode (continuous acquisition)
            mvsdk.CameraSetTriggerMode(self.hCamera, 0)

            # Set manual exposure
            mvsdk.CameraSetAeState(self.hCamera, 0)  # Disable auto exposure
            exposure_us = int(self.camera_config.exposure_ms * 1000)  # Convert ms to microseconds
            mvsdk.CameraSetExposureTime(self.hCamera, exposure_us)

            # Set analog gain
            gain_value = int(self.camera_config.gain * 100)  # Convert to camera units
            mvsdk.CameraSetAnalogGain(self.hCamera, gain_value)

            # Configure image quality settings
            self._configure_image_quality()

            # Configure noise reduction
            self._configure_noise_reduction()

            # Configure color settings (for color cameras)
            if not self.monoCamera:
                self._configure_color_settings()

            # Configure advanced settings
            self._configure_advanced_settings()

            self.logger.info(f"Camera settings configured - Exposure: {exposure_us}μs, Gain: {gain_value}")

        except Exception as e:
            self.logger.warning(f"Error configuring camera settings: {e}")

    def _configure_image_quality(self) -> None:
        """Configure image quality settings"""
        try:
            # Set sharpness (0-200, default 100)
            mvsdk.CameraSetSharpness(self.hCamera, self.camera_config.sharpness)

            # Set contrast (0-200, default 100)
            mvsdk.CameraSetContrast(self.hCamera, self.camera_config.contrast)

            # Set gamma (0-300, default 100)
            mvsdk.CameraSetGamma(self.hCamera, self.camera_config.gamma)

            # Set saturation for color cameras (0-200, default 100)
            if not self.monoCamera:
                mvsdk.CameraSetSaturation(self.hCamera, self.camera_config.saturation)

            self.logger.info(f"Image quality configured - Sharpness: {self.camera_config.sharpness}, " f"Contrast: {self.camera_config.contrast}, Gamma: {self.camera_config.gamma}")

        except Exception as e:
            self.logger.warning(f"Error configuring image quality: {e}")

    def _configure_noise_reduction(self) -> None:
        """Configure noise reduction settings"""
        try:
            # Enable/disable basic noise filter
            mvsdk.CameraSetNoiseFilter(self.hCamera, self.camera_config.noise_filter_enabled)

            # Configure 3D denoising if enabled
            if self.camera_config.denoise_3d_enabled:
                # Enable 3D denoising with default parameters (3 frames, equal weights)
                mvsdk.CameraSetDenoise3DParams(self.hCamera, True, 3, None)
                self.logger.info("3D denoising enabled")
            else:
                mvsdk.CameraSetDenoise3DParams(self.hCamera, False, 2, None)

            self.logger.info(f"Noise reduction configured - Filter: {self.camera_config.noise_filter_enabled}, " f"3D Denoise: {self.camera_config.denoise_3d_enabled}")

        except Exception as e:
            self.logger.warning(f"Error configuring noise reduction: {e}")

    def _configure_color_settings(self) -> None:
        """Configure color settings for color cameras"""
        try:
            # Set white balance mode
            mvsdk.CameraSetWbMode(self.hCamera, self.camera_config.auto_white_balance)

            # Set color temperature preset if not using auto white balance
            if not self.camera_config.auto_white_balance:
                mvsdk.CameraSetPresetClrTemp(self.hCamera, self.camera_config.color_temperature_preset)

                # Set manual RGB gains for manual white balance
                red_gain = int(self.camera_config.wb_red_gain * 100)  # Convert to camera units
                green_gain = int(self.camera_config.wb_green_gain * 100)
                blue_gain = int(self.camera_config.wb_blue_gain * 100)
                mvsdk.CameraSetUserClrTempGain(self.hCamera, red_gain, green_gain, blue_gain)

            self.logger.info(f"Color settings configured - Auto WB: {self.camera_config.auto_white_balance}, " f"Color Temp Preset: {self.camera_config.color_temperature_preset}, " f"RGB Gains: R={self.camera_config.wb_red_gain}, G={self.camera_config.wb_green_gain}, B={self.camera_config.wb_blue_gain}")

        except Exception as e:
            self.logger.warning(f"Error configuring color settings: {e}")

    def _configure_advanced_settings(self) -> None:
        """Configure advanced camera settings"""
        try:
            # Set anti-flicker
            mvsdk.CameraSetAntiFlick(self.hCamera, self.camera_config.anti_flicker_enabled)

            # Set light frequency (0=50Hz, 1=60Hz)
            mvsdk.CameraSetLightFrequency(self.hCamera, self.camera_config.light_frequency)

            # Configure HDR if enabled (check if HDR functions are available)
            try:
                if self.camera_config.hdr_enabled:
                    mvsdk.CameraSetHDR(self.hCamera, 1)  # Enable HDR
                    mvsdk.CameraSetHDRGainMode(self.hCamera, self.camera_config.hdr_gain_mode)
                    self.logger.info(f"HDR enabled with gain mode: {self.camera_config.hdr_gain_mode}")
                else:
                    mvsdk.CameraSetHDR(self.hCamera, 0)  # Disable HDR
            except AttributeError:
                self.logger.info("HDR functions not available in this SDK version, skipping HDR configuration")

            self.logger.info(f"Advanced settings configured - Anti-flicker: {self.camera_config.anti_flicker_enabled}, " f"Light Freq: {self.camera_config.light_frequency}Hz, HDR: {self.camera_config.hdr_enabled}")

        except Exception as e:
            self.logger.warning(f"Error configuring advanced settings: {e}")

    def update_camera_settings(self, exposure_ms: Optional[float] = None, gain: Optional[float] = None, target_fps: Optional[float] = None) -> bool:
        """Update camera settings dynamically"""
        if not self.hCamera:
            self.logger.error("Camera not initialized")
            return False

        try:
            settings_updated = False

            # Update exposure if provided
            if exposure_ms is not None:
                mvsdk.CameraSetAeState(self.hCamera, 0)  # Disable auto exposure
                exposure_us = int(exposure_ms * 1000)  # Convert ms to microseconds
                mvsdk.CameraSetExposureTime(self.hCamera, exposure_us)
                self.camera_config.exposure_ms = exposure_ms
                self.logger.info(f"Updated exposure time: {exposure_ms}ms")
                settings_updated = True

            # Update gain if provided
            if gain is not None:
                gain_value = int(gain * 100)  # Convert to camera units
                mvsdk.CameraSetAnalogGain(self.hCamera, gain_value)
                self.camera_config.gain = gain
                self.logger.info(f"Updated gain: {gain}x")
                settings_updated = True

            # Update target FPS if provided
            if target_fps is not None:
                self.camera_config.target_fps = target_fps
                self.logger.info(f"Updated target FPS: {target_fps}")
                settings_updated = True

            return settings_updated

        except Exception as e:
            self.logger.error(f"Error updating camera settings: {e}")
            return False

    def update_advanced_camera_settings(self, **kwargs) -> bool:
        """Update advanced camera settings dynamically"""
        if not self.hCamera:
            self.logger.error("Camera not initialized")
            return False

        try:
            settings_updated = False

            # Update basic settings
            if "exposure_ms" in kwargs and kwargs["exposure_ms"] is not None:
                mvsdk.CameraSetAeState(self.hCamera, 0)
                exposure_us = int(kwargs["exposure_ms"] * 1000)
                mvsdk.CameraSetExposureTime(self.hCamera, exposure_us)
                self.camera_config.exposure_ms = kwargs["exposure_ms"]
                settings_updated = True

            if "gain" in kwargs and kwargs["gain"] is not None:
                gain_value = int(kwargs["gain"] * 100)
                mvsdk.CameraSetAnalogGain(self.hCamera, gain_value)
                self.camera_config.gain = kwargs["gain"]
                settings_updated = True

            if "target_fps" in kwargs and kwargs["target_fps"] is not None:
                self.camera_config.target_fps = kwargs["target_fps"]
                settings_updated = True

            # Update image quality settings
            if "sharpness" in kwargs and kwargs["sharpness"] is not None:
                mvsdk.CameraSetSharpness(self.hCamera, kwargs["sharpness"])
                self.camera_config.sharpness = kwargs["sharpness"]
                settings_updated = True

            if "contrast" in kwargs and kwargs["contrast"] is not None:
                mvsdk.CameraSetContrast(self.hCamera, kwargs["contrast"])
                self.camera_config.contrast = kwargs["contrast"]
                settings_updated = True

            if "gamma" in kwargs and kwargs["gamma"] is not None:
                mvsdk.CameraSetGamma(self.hCamera, kwargs["gamma"])
                self.camera_config.gamma = kwargs["gamma"]
                settings_updated = True

            if "saturation" in kwargs and kwargs["saturation"] is not None and not self.monoCamera:
                mvsdk.CameraSetSaturation(self.hCamera, kwargs["saturation"])
                self.camera_config.saturation = kwargs["saturation"]
                settings_updated = True

            # Update noise reduction settings
            if "noise_filter_enabled" in kwargs and kwargs["noise_filter_enabled"] is not None:
                # Note: Noise filter settings may require camera restart to take effect
                self.camera_config.noise_filter_enabled = kwargs["noise_filter_enabled"]
                settings_updated = True

            if "denoise_3d_enabled" in kwargs and kwargs["denoise_3d_enabled"] is not None:
                # Note: 3D denoise settings may require camera restart to take effect
                self.camera_config.denoise_3d_enabled = kwargs["denoise_3d_enabled"]
                settings_updated = True

            # Update color settings (for color cameras)
            if not self.monoCamera:
                if "auto_white_balance" in kwargs and kwargs["auto_white_balance"] is not None:
                    mvsdk.CameraSetWbMode(self.hCamera, kwargs["auto_white_balance"])
                    self.camera_config.auto_white_balance = kwargs["auto_white_balance"]
                    settings_updated = True

                if "color_temperature_preset" in kwargs and kwargs["color_temperature_preset"] is not None:
                    if not self.camera_config.auto_white_balance:
                        mvsdk.CameraSetPresetClrTemp(self.hCamera, kwargs["color_temperature_preset"])
                    self.camera_config.color_temperature_preset = kwargs["color_temperature_preset"]
                    settings_updated = True

                # Update RGB gains for manual white balance
                rgb_gains_updated = False
                if "wb_red_gain" in kwargs and kwargs["wb_red_gain"] is not None:
                    self.camera_config.wb_red_gain = kwargs["wb_red_gain"]
                    rgb_gains_updated = True
                    settings_updated = True

                if "wb_green_gain" in kwargs and kwargs["wb_green_gain"] is not None:
                    self.camera_config.wb_green_gain = kwargs["wb_green_gain"]
                    rgb_gains_updated = True
                    settings_updated = True

                if "wb_blue_gain" in kwargs and kwargs["wb_blue_gain"] is not None:
                    self.camera_config.wb_blue_gain = kwargs["wb_blue_gain"]
                    rgb_gains_updated = True
                    settings_updated = True

                # Apply RGB gains if any were updated and we're in manual white balance mode
                if rgb_gains_updated and not self.camera_config.auto_white_balance:
                    red_gain = int(self.camera_config.wb_red_gain * 100)
                    green_gain = int(self.camera_config.wb_green_gain * 100)
                    blue_gain = int(self.camera_config.wb_blue_gain * 100)
                    mvsdk.CameraSetUserClrTempGain(self.hCamera, red_gain, green_gain, blue_gain)

            # Update advanced settings
            if "anti_flicker_enabled" in kwargs and kwargs["anti_flicker_enabled"] is not None:
                mvsdk.CameraSetAntiFlick(self.hCamera, kwargs["anti_flicker_enabled"])
                self.camera_config.anti_flicker_enabled = kwargs["anti_flicker_enabled"]
                settings_updated = True

            if "light_frequency" in kwargs and kwargs["light_frequency"] is not None:
                mvsdk.CameraSetLightFrequency(self.hCamera, kwargs["light_frequency"])
                self.camera_config.light_frequency = kwargs["light_frequency"]
                settings_updated = True

            # Update HDR settings (if supported)
            if "hdr_enabled" in kwargs and kwargs["hdr_enabled"] is not None:
                try:
                    mvsdk.CameraSetHDR(self.hCamera, 1 if kwargs["hdr_enabled"] else 0)
                    self.camera_config.hdr_enabled = kwargs["hdr_enabled"]
                    settings_updated = True
                except AttributeError:
                    self.logger.warning("HDR functions not available in this SDK version")

            if "hdr_gain_mode" in kwargs and kwargs["hdr_gain_mode"] is not None:
                try:
                    if self.camera_config.hdr_enabled:
                        mvsdk.CameraSetHDRGainMode(self.hCamera, kwargs["hdr_gain_mode"])
                    self.camera_config.hdr_gain_mode = kwargs["hdr_gain_mode"]
                    settings_updated = True
                except AttributeError:
                    self.logger.warning("HDR gain mode functions not available in this SDK version")

            if settings_updated:
                updated_settings = [k for k, v in kwargs.items() if v is not None]
                self.logger.info(f"Updated camera settings: {updated_settings}")

            return settings_updated

        except Exception as e:
            self.logger.error(f"Error updating advanced camera settings: {e}")
            return False

    def start_recording(self, filename: str) -> bool:
        """Start video recording"""
        with self._lock:
            if self.recording:
                self.logger.warning("Already recording!")
                return False

            # Initialize camera if not already initialized (lazy initialization)
            if not self.hCamera:
                self.logger.info("Camera not initialized, initializing now...")
                if not self._initialize_camera():
                    self.logger.error("Failed to initialize camera for recording")
                    return False

            try:
                # Prepare output path
                output_path = os.path.join(self.camera_config.storage_path, filename)
                Path(self.camera_config.storage_path).mkdir(parents=True, exist_ok=True)

                # Test camera capture before starting recording
                if not self._test_camera_capture():
                    self.logger.error("Camera capture test failed")
                    return False

                # Initialize recording state
                self.output_filename = output_path
                self.frame_count = 0
                self.start_time = now_atlanta()  # Use Atlanta timezone
                self._stop_recording_event.clear()

                # Start recording thread
                self._recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
                self._recording_thread.start()

                # Update state
                self.recording = True
                recording_id = self.state_manager.start_recording(self.camera_config.name, output_path)

                # Publish event
                publish_recording_started(self.camera_config.name, output_path)

                self.logger.info(f"Started recording to: {output_path}")
                return True

            except Exception as e:
                self.logger.error(f"Error starting recording: {e}")
                publish_recording_error(self.camera_config.name, str(e))
                return False

    def _test_camera_capture(self) -> bool:
        """Test if camera can capture frames"""
        try:
            # Try to capture one frame
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 1000)  # 1 second timeout
            mvsdk.CameraImageProcess(self.hCamera, pRawData, self.frame_buffer, FrameHead)
            mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)
            return True
        except Exception as e:
            self.logger.error(f"Camera capture test failed: {e}")
            return False

    def stop_recording(self) -> bool:
        """Stop video recording"""
        with self._lock:
            if not self.recording:
                self.logger.warning("Not currently recording")
                return False

            try:
                # Signal recording thread to stop
                self._stop_recording_event.set()

                # Wait for recording thread to finish
                if self._recording_thread and self._recording_thread.is_alive():
                    self._recording_thread.join(timeout=5)

                # Update state
                self.recording = False

                # Calculate duration and file size
                duration = 0
                file_size = 0
                if self.start_time:
                    duration = (now_atlanta() - self.start_time).total_seconds()

                if self.output_filename and os.path.exists(self.output_filename):
                    file_size = os.path.getsize(self.output_filename)

                # Update state manager
                if self.output_filename:
                    self.state_manager.stop_recording(self.output_filename, file_size, self.frame_count)

                # Publish event
                publish_recording_stopped(self.camera_config.name, self.output_filename or "unknown", duration)

                # Clean up camera resources after recording (lazy cleanup)
                self._cleanup_camera()
                self.logger.info("Camera resources cleaned up after recording")

                self.logger.info(f"Stopped recording - Duration: {duration:.1f}s, Frames: {self.frame_count}")
                return True

            except Exception as e:
                self.logger.error(f"Error stopping recording: {e}")
                return False

    def _recording_loop(self) -> None:
        """Main recording loop running in separate thread"""
        try:
            # Initialize video writer
            if not self._initialize_video_writer():
                self.logger.error("Failed to initialize video writer")
                return

            self.logger.info("Recording loop started")

            while not self._stop_recording_event.is_set():
                try:
                    # Capture frame
                    pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)  # 200ms timeout

                    # Process frame
                    mvsdk.CameraImageProcess(self.hCamera, pRawData, self.frame_buffer, FrameHead)

                    # Convert to OpenCV format
                    frame = self._convert_frame_to_opencv(FrameHead)

                    # Write frame to video
                    if frame is not None and self.video_writer:
                        self.video_writer.write(frame)
                        self.frame_count += 1

                    # Release buffer
                    mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)

                    # Control frame rate (skip sleep if target_fps is 0 for maximum speed)
                    if self.camera_config.target_fps > 0:
                        time.sleep(1.0 / self.camera_config.target_fps)

                except mvsdk.CameraException as e:
                    if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
                        continue  # Timeout is normal, continue
                    else:
                        self.logger.error(f"Camera error during recording: {e.message}")
                        break
                except Exception as e:
                    self.logger.error(f"Error in recording loop: {e}")
                    break

            self.logger.info("Recording loop ended")

        except Exception as e:
            self.logger.error(f"Fatal error in recording loop: {e}")
            publish_recording_error(self.camera_config.name, str(e))
        finally:
            self._cleanup_recording()

    def _initialize_video_writer(self) -> bool:
        """Initialize OpenCV video writer"""
        try:
            # Get frame dimensions by capturing a test frame
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 1000)
            mvsdk.CameraImageProcess(self.hCamera, pRawData, self.frame_buffer, FrameHead)
            mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)

            # Set up video writer with configured codec
            fourcc = cv2.VideoWriter_fourcc(*self.camera_config.video_codec)
            frame_size = (FrameHead.iWidth, FrameHead.iHeight)

            # Use 30 FPS for video writer if target_fps is 0 (unlimited)
            video_fps = self.camera_config.target_fps if self.camera_config.target_fps > 0 else 30.0

            # Create video writer with quality settings
            self.video_writer = cv2.VideoWriter(self.output_filename, fourcc, video_fps, frame_size)

            # Set quality if supported (for some codecs)
            if hasattr(self.video_writer, "set") and self.camera_config.video_quality:
                try:
                    self.video_writer.set(cv2.VIDEOWRITER_PROP_QUALITY, self.camera_config.video_quality)
                except:
                    pass  # Quality setting not supported for this codec

            if not self.video_writer.isOpened():
                self.logger.error(f"Failed to open video writer for {self.output_filename}")
                return False

            self.logger.info(f"Video writer initialized - Size: {frame_size}, FPS: {self.camera_config.target_fps}")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing video writer: {e}")
            return False

    def _convert_frame_to_opencv(self, frame_head) -> Optional[np.ndarray]:
        """Convert camera frame to OpenCV format"""
        try:
            # Convert the frame buffer memory address to a proper buffer
            # that numpy can work with using mvsdk.c_ubyte
            frame_data_buffer = (mvsdk.c_ubyte * frame_head.uBytes).from_address(self.frame_buffer)

            # Handle different bit depths
            if self.camera_config.bit_depth > 8:
                # For >8-bit, data is stored as 16-bit values
                frame_data = np.frombuffer(frame_data_buffer, dtype=np.uint16)

                if self.monoCamera:
                    # Monochrome camera - convert to 8-bit BGR for video
                    frame = frame_data.reshape((frame_head.iHeight, frame_head.iWidth))
                    # Scale down to 8-bit (simple right shift)
                    frame_8bit = (frame >> (self.camera_config.bit_depth - 8)).astype(np.uint8)
                    frame_bgr = cv2.cvtColor(frame_8bit, cv2.COLOR_GRAY2BGR)
                else:
                    # Color camera - convert to 8-bit BGR
                    frame = frame_data.reshape((frame_head.iHeight, frame_head.iWidth, 3))
                    # Scale down to 8-bit
                    frame_bgr = (frame >> (self.camera_config.bit_depth - 8)).astype(np.uint8)
            else:
                # 8-bit data
                frame_data = np.frombuffer(frame_data_buffer, dtype=np.uint8)

                if self.monoCamera:
                    # Monochrome camera - convert to BGR
                    frame = frame_data.reshape((frame_head.iHeight, frame_head.iWidth))
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                else:
                    # Color camera - already in BGR format
                    frame_bgr = frame_data.reshape((frame_head.iHeight, frame_head.iWidth, 3))

            return frame_bgr

        except Exception as e:
            self.logger.error(f"Error converting frame: {e}")
            return None

    def _cleanup_recording(self) -> None:
        """Clean up recording resources"""
        try:
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None

            self.recording = False

        except Exception as e:
            self.logger.error(f"Error during recording cleanup: {e}")

    def test_connection(self) -> bool:
        """Test camera connection"""
        try:
            if self.hCamera is None:
                self.logger.error("Camera not initialized")
                return False

            # Test connection using SDK function
            result = mvsdk.CameraConnectTest(self.hCamera)
            if result == 0:  # CAMERA_STATUS_SUCCESS
                self.logger.info("Camera connection test passed")
                return True
            else:
                self.logger.error(f"Camera connection test failed with code: {result}")
                return False

        except Exception as e:
            self.logger.error(f"Error testing camera connection: {e}")
            return False

    def reconnect(self) -> bool:
        """Attempt to reconnect to the camera"""
        try:
            if self.hCamera is None:
                self.logger.error("Camera not initialized, cannot reconnect")
                return False

            self.logger.info("Attempting to reconnect camera...")

            # Stop any ongoing operations
            if self.recording:
                self.logger.info("Stopping recording before reconnect")
                self.stop_recording()

            # Attempt reconnection using SDK function
            result = mvsdk.CameraReConnect(self.hCamera)
            if result == 0:  # CAMERA_STATUS_SUCCESS
                self.logger.info("Camera reconnected successfully")

                # Restart camera if it was playing
                try:
                    mvsdk.CameraPlay(self.hCamera)
                    self.logger.info("Camera restarted after reconnection")
                except Exception as e:
                    self.logger.warning(f"Failed to restart camera after reconnection: {e}")

                return True
            else:
                self.logger.error(f"Camera reconnection failed with code: {result}")
                return False

        except Exception as e:
            self.logger.error(f"Error during camera reconnection: {e}")
            return False

    def restart_grab(self) -> bool:
        """Restart the camera grab process"""
        try:
            if self.hCamera is None:
                self.logger.error("Camera not initialized")
                return False

            self.logger.info("Restarting camera grab process...")

            # Stop any ongoing recording
            if self.recording:
                self.logger.info("Stopping recording before restart")
                self.stop_recording()

            # Restart grab using SDK function
            result = mvsdk.CameraRestartGrab(self.hCamera)
            if result == 0:  # CAMERA_STATUS_SUCCESS
                self.logger.info("Camera grab restarted successfully")
                return True
            else:
                self.logger.error(f"Camera grab restart failed with code: {result}")
                return False

        except Exception as e:
            self.logger.error(f"Error restarting camera grab: {e}")
            return False

    def reset_timestamp(self) -> bool:
        """Reset camera timestamp"""
        try:
            if self.hCamera is None:
                self.logger.error("Camera not initialized")
                return False

            self.logger.info("Resetting camera timestamp...")

            result = mvsdk.CameraRstTimeStamp(self.hCamera)
            if result == 0:  # CAMERA_STATUS_SUCCESS
                self.logger.info("Camera timestamp reset successfully")
                return True
            else:
                self.logger.error(f"Camera timestamp reset failed with code: {result}")
                return False

        except Exception as e:
            self.logger.error(f"Error resetting camera timestamp: {e}")
            return False

    def full_reset(self) -> bool:
        """Perform a full camera reset (uninitialize and reinitialize)"""
        try:
            self.logger.info("Performing full camera reset...")

            # Stop any ongoing recording
            if self.recording:
                self.logger.info("Stopping recording before reset")
                self.stop_recording()

            # Store device info for reinitialization
            device_info = self.device_info

            # Cleanup current camera
            self._cleanup_camera()

            # Wait a moment
            time.sleep(1)

            # Reinitialize camera
            self.device_info = device_info
            success = self._initialize_camera()

            if success:
                self.logger.info("Full camera reset completed successfully")
                return True
            else:
                self.logger.error("Full camera reset failed during reinitialization")
                return False

        except Exception as e:
            self.logger.error(f"Error during full camera reset: {e}")
            return False

    def _cleanup_camera(self) -> None:
        """Clean up camera resources"""
        try:
            # Stop camera if running
            if self.hCamera is not None:
                try:
                    mvsdk.CameraStop(self.hCamera)
                except:
                    pass  # Ignore errors during stop

                # Uninitialize camera
                try:
                    mvsdk.CameraUnInit(self.hCamera)
                except:
                    pass  # Ignore errors during uninit

                self.hCamera = None

            # Free frame buffer
            if self.frame_buffer is not None:
                try:
                    mvsdk.CameraAlignFree(self.frame_buffer)
                except:
                    pass  # Ignore errors during free

                self.frame_buffer = None

            self.logger.info("Camera resources cleaned up")

        except Exception as e:
            self.logger.error(f"Error during camera cleanup: {e}")

    def cleanup(self) -> None:
        """Clean up camera resources"""
        try:
            # Stop recording if active
            if self.recording:
                self.stop_recording()

            # Clean up camera
            if self.hCamera:
                mvsdk.CameraUnInit(self.hCamera)
                self.hCamera = None

            # Free frame buffer
            if self.frame_buffer:
                mvsdk.CameraAlignFree(self.frame_buffer)
                self.frame_buffer = None

            self.logger.info("Camera resources cleaned up")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self.recording

    def get_status(self) -> Dict[str, Any]:
        """Get recorder status"""
        return {"camera_name": self.camera_config.name, "is_recording": self.recording, "current_file": self.output_filename, "frame_count": self.frame_count, "start_time": self.start_time.isoformat() if self.start_time else None, "camera_initialized": self.hCamera is not None, "storage_path": self.camera_config.storage_path}
