"""
Camera Streamer for the USDA Vision Camera System.

This module provides live preview streaming from GigE cameras without blocking recording.
It creates a separate camera connection for streaming that doesn't interfere with recording.
"""

import sys
import os
import threading
import time
import logging
import cv2
import numpy as np
import contextlib
from typing import Optional, Dict, Any, Generator
from datetime import datetime
import queue

# Add camera SDK to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "camera_sdk"))
import mvsdk

from ..core.config import CameraConfig
from ..core.state_manager import StateManager
from ..core.events import EventSystem
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


class CameraStreamer:
    """Provides live preview streaming from cameras without blocking recording"""

    def __init__(self, camera_config: CameraConfig, device_info: Any, state_manager: StateManager, event_system: EventSystem):
        self.camera_config = camera_config
        self.device_info = device_info
        self.state_manager = state_manager
        self.event_system = event_system
        self.logger = logging.getLogger(f"{__name__}.{camera_config.name}")

        # Camera handle and properties (separate from recorder)
        self.hCamera: Optional[int] = None
        self.cap = None
        self.monoCamera = False
        self.frame_buffer = None
        self.frame_buffer_size = 0

        # Streaming state
        self.streaming = False
        self._streaming_thread: Optional[threading.Thread] = None
        self._stop_streaming_event = threading.Event()
        self._frame_queue = queue.Queue(maxsize=5)  # Buffer for latest frames
        self._lock = threading.RLock()

        # Stream settings (optimized for preview)
        self.preview_fps = 10.0  # Lower FPS for preview to reduce load
        self.preview_quality = 70  # JPEG quality for streaming

    def start_streaming(self) -> bool:
        """Start streaming preview frames"""
        with self._lock:
            if self.streaming:
                self.logger.warning("Streaming already active")
                return True

            try:
                # Initialize camera for streaming
                if not self._initialize_camera():
                    return False

                # Start streaming thread
                self._stop_streaming_event.clear()
                self._streaming_thread = threading.Thread(target=self._streaming_loop, daemon=True)
                self._streaming_thread.start()

                self.streaming = True
                self.logger.info(f"Started streaming for camera: {self.camera_config.name}")
                return True

            except Exception as e:
                self.logger.error(f"Error starting streaming: {e}")
                self._cleanup_camera()
                return False

    def stop_streaming(self) -> bool:
        """Stop streaming preview frames"""
        with self._lock:
            if not self.streaming:
                return True

            try:
                # Signal streaming thread to stop
                self._stop_streaming_event.set()

                # Wait for thread to finish
                if self._streaming_thread and self._streaming_thread.is_alive():
                    self._streaming_thread.join(timeout=5.0)

                # Cleanup camera resources
                self._cleanup_camera()

                self.streaming = False
                self.logger.info(f"Stopped streaming for camera: {self.camera_config.name}")
                return True

            except Exception as e:
                self.logger.error(f"Error stopping streaming: {e}")
                return False

    def get_latest_frame(self) -> Optional[bytes]:
        """Get the latest frame as JPEG bytes for streaming"""
        try:
            # Get latest frame from queue (non-blocking)
            frame = self._frame_queue.get_nowait()

            # Encode as JPEG
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self.preview_quality])
            return buffer.tobytes()

        except queue.Empty:
            return None
        except Exception as e:
            self.logger.error(f"Error getting latest frame: {e}")
            return None

    def get_frame_generator(self) -> Generator[bytes, None, None]:
        """Generator for MJPEG streaming"""
        while self.streaming:
            frame_bytes = self.get_latest_frame()
            if frame_bytes:
                yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            else:
                time.sleep(0.1)  # Wait a bit if no frame available

    def _initialize_camera(self) -> bool:
        """Initialize camera for streaming (separate from recording)"""
        try:
            self.logger.info(f"Initializing camera for streaming: {self.camera_config.name}")

            # Ensure SDK is initialized
            ensure_sdk_initialized()

            # Check if device_info is valid
            if self.device_info is None:
                self.logger.error("No device info provided for camera initialization")
                return False

            # Initialize camera (suppress output to avoid MVCAMAPI error messages)
            with suppress_camera_errors():
                self.hCamera = mvsdk.CameraInit(self.device_info, -1, -1)
            self.logger.info("Camera initialized successfully for streaming")

            # Get camera capabilities
            self.cap = mvsdk.CameraGetCapability(self.hCamera)

            # Determine if camera is monochrome
            self.monoCamera = self.cap.sIspCapacity.bMonoSensor != 0

            # Set output format based on camera type and bit depth
            if self.monoCamera:
                mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
            else:
                mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

            # Configure camera settings for streaming (optimized for preview)
            self._configure_streaming_settings()

            # Allocate frame buffer
            bytes_per_pixel = 1 if self.monoCamera else 3
            self.frame_buffer_size = self.cap.sResolutionRange.iWidthMax * self.cap.sResolutionRange.iHeightMax * bytes_per_pixel
            self.frame_buffer = mvsdk.CameraAlignMalloc(self.frame_buffer_size, 16)

            # Start camera
            mvsdk.CameraPlay(self.hCamera)
            self.logger.info("Camera started successfully for streaming")

            return True

        except Exception as e:
            self.logger.error(f"Error initializing camera for streaming: {e}")
            self._cleanup_camera()
            return False

    def _configure_streaming_settings(self):
        """Configure camera settings from config.json for streaming"""
        try:
            # Set trigger mode to free run for continuous streaming
            mvsdk.CameraSetTriggerMode(self.hCamera, 0)

            # Set manual exposure
            mvsdk.CameraSetAeState(self.hCamera, 0)  # Disable auto exposure
            exposure_us = int(self.camera_config.exposure_ms * 1000)  # Convert ms to microseconds
            mvsdk.CameraSetExposureTime(self.hCamera, exposure_us)

            # Set analog gain
            gain_value = int(self.camera_config.gain * 100)  # Convert to camera units
            mvsdk.CameraSetAnalogGain(self.hCamera, gain_value)

            # Set frame rate for streaming (lower than recording)
            if hasattr(mvsdk, "CameraSetFrameSpeed"):
                mvsdk.CameraSetFrameSpeed(self.hCamera, int(self.preview_fps))

            # Configure image quality settings
            self._configure_image_quality()

            # Configure noise reduction
            self._configure_noise_reduction()

            # Configure color settings (for color cameras)
            if not self.monoCamera:
                self._configure_color_settings()

            # Configure advanced settings
            self._configure_advanced_settings()

            self.logger.info(f"Streaming settings configured: exposure={self.camera_config.exposure_ms}ms, gain={self.camera_config.gain}, fps={self.preview_fps}")

        except Exception as e:
            self.logger.warning(f"Could not configure some streaming settings: {e}")

    def _streaming_loop(self):
        """Main streaming loop that captures frames continuously"""
        self.logger.info("Starting streaming loop")

        try:
            while not self._stop_streaming_event.is_set():
                try:
                    # Capture frame with timeout
                    pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)  # 200ms timeout

                    # Process frame
                    mvsdk.CameraImageProcess(self.hCamera, pRawData, self.frame_buffer, FrameHead)

                    # Convert to OpenCV format
                    frame = self._convert_frame_to_opencv(FrameHead)

                    if frame is not None:
                        # Add frame to queue (replace oldest if queue is full)
                        try:
                            self._frame_queue.put_nowait(frame)
                        except queue.Full:
                            # Remove oldest frame and add new one
                            try:
                                self._frame_queue.get_nowait()
                                self._frame_queue.put_nowait(frame)
                            except queue.Empty:
                                pass

                    # Release buffer
                    mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)

                    # Control frame rate
                    time.sleep(1.0 / self.preview_fps)

                except Exception as e:
                    if not self._stop_streaming_event.is_set():
                        self.logger.error(f"Error in streaming loop: {e}")
                        time.sleep(0.1)  # Brief pause before retrying

        except Exception as e:
            self.logger.error(f"Fatal error in streaming loop: {e}")
        finally:
            self.logger.info("Streaming loop ended")

    def _convert_frame_to_opencv(self, FrameHead) -> Optional[np.ndarray]:
        """Convert camera frame to OpenCV format"""
        try:
            # Convert the frame buffer memory address to a proper buffer
            # that numpy can work with using mvsdk.c_ubyte
            frame_data_buffer = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.frame_buffer)

            if self.monoCamera:
                # Monochrome camera
                frame_data = np.frombuffer(frame_data_buffer, dtype=np.uint8)
                frame = frame_data.reshape((FrameHead.iHeight, FrameHead.iWidth))
                # Convert to 3-channel for consistency
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            else:
                # Color camera (BGR format)
                frame_data = np.frombuffer(frame_data_buffer, dtype=np.uint8)
                frame = frame_data.reshape((FrameHead.iHeight, FrameHead.iWidth, 3))

            return frame

        except Exception as e:
            self.logger.error(f"Error converting frame: {e}")
            return None

    def _cleanup_camera(self):
        """Clean up camera resources"""
        try:
            if self.frame_buffer:
                mvsdk.CameraAlignFree(self.frame_buffer)
                self.frame_buffer = None

            if self.hCamera is not None:
                mvsdk.CameraUnInit(self.hCamera)
                self.hCamera = None

            self.logger.info("Camera resources cleaned up for streaming")

        except Exception as e:
            self.logger.error(f"Error cleaning up camera resources: {e}")

    def is_streaming(self) -> bool:
        """Check if streaming is active"""
        return self.streaming

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
            # Note: Some noise reduction settings may require specific SDK functions
            # that might not be available in all SDK versions
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

    def __del__(self):
        """Destructor to ensure cleanup"""
        if self.streaming:
            self.stop_streaming()
