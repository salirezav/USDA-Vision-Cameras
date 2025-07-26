"""
Camera Recorder for the USDA Vision Camera System.

This module handles video recording from GigE cameras using the python demo library (mvsdk).
"""

import sys
import os
import threading
import time
import logging
import cv2
import numpy as np
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

# Add python demo to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'python demo'))
import mvsdk

from ..core.config import CameraConfig
from ..core.state_manager import StateManager
from ..core.events import EventSystem, publish_recording_started, publish_recording_stopped, publish_recording_error
from ..core.timezone_utils import now_atlanta, format_filename_timestamp


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
        
        # Initialize camera
        self._initialize_camera()
    
    def _initialize_camera(self) -> bool:
        """Initialize the camera with configured settings"""
        try:
            self.logger.info(f"Initializing camera: {self.camera_config.name}")

            # Check if device_info is valid
            if self.device_info is None:
                self.logger.error("No device info provided for camera initialization")
                return False

            # Initialize camera
            self.hCamera = mvsdk.CameraInit(self.device_info, -1, -1)
            self.logger.info("Camera initialized successfully")

            # Get camera capabilities
            self.cap = mvsdk.CameraGetCapability(self.hCamera)
            self.monoCamera = self.cap.sIspCapacity.bMonoSensor != 0
            self.logger.info(f"Camera type: {'Monochrome' if self.monoCamera else 'Color'}")

            # Set output format
            if self.monoCamera:
                mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
            else:
                mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

            # Configure camera settings
            self._configure_camera_settings()

            # Allocate frame buffer
            self.frame_buffer_size = (self.cap.sResolutionRange.iWidthMax *
                                    self.cap.sResolutionRange.iHeightMax *
                                    (1 if self.monoCamera else 3))
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
            
            self.logger.info(f"Camera settings configured - Exposure: {exposure_us}μs, Gain: {gain_value}")
            
        except Exception as e:
            self.logger.warning(f"Error configuring camera settings: {e}")
    
    def start_recording(self, filename: str) -> bool:
        """Start video recording"""
        with self._lock:
            if self.recording:
                self.logger.warning("Already recording!")
                return False
            
            if not self.hCamera:
                self.logger.error("Camera not initialized")
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
                publish_recording_stopped(
                    self.camera_config.name,
                    self.output_filename or "unknown",
                    duration
                )

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

            # Set up video writer
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            frame_size = (FrameHead.iWidth, FrameHead.iHeight)

            # Use 30 FPS for video writer if target_fps is 0 (unlimited)
            video_fps = self.camera_config.target_fps if self.camera_config.target_fps > 0 else 30.0

            self.video_writer = cv2.VideoWriter(
                self.output_filename,
                fourcc,
                video_fps,
                frame_size
            )

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
        return {
            "camera_name": self.camera_config.name,
            "is_recording": self.recording,
            "current_file": self.output_filename,
            "frame_count": self.frame_count,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "camera_initialized": self.hCamera is not None,
            "storage_path": self.camera_config.storage_path
        }
