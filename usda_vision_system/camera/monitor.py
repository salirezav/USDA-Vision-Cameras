"""
Camera Monitor for the USDA Vision Camera System.

This module monitors camera status and availability at regular intervals.
"""

import sys
import os
import threading
import time
import logging
import contextlib
from typing import Dict, List, Optional, Any

# Add python demo to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "python demo"))
import mvsdk

from ..core.config import Config
from ..core.state_manager import StateManager, CameraStatus
from ..core.events import EventSystem, publish_camera_status_changed
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


class CameraMonitor:
    """Monitors camera status and availability"""

    def __init__(self, config: Config, state_manager: StateManager, event_system: EventSystem, camera_manager=None):
        self.config = config
        self.state_manager = state_manager
        self.event_system = event_system
        self.camera_manager = camera_manager  # Reference to camera manager
        self.logger = logging.getLogger(__name__)

        # Monitoring settings
        self.check_interval = config.system.camera_check_interval_seconds

        # Threading
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Status tracking
        self.last_check_time: Optional[float] = None
        self.check_count = 0
        self.error_count = 0

    def start(self) -> bool:
        """Start camera monitoring"""
        if self.running:
            self.logger.warning("Camera monitor is already running")
            return True

        self.logger.info(f"Starting camera monitor (check interval: {self.check_interval}s)")
        self.running = True
        self._stop_event.clear()

        # Start monitoring thread
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()

        return True

    def stop(self) -> None:
        """Stop camera monitoring"""
        if not self.running:
            return

        self.logger.info("Stopping camera monitor...")
        self.running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        self.logger.info("Camera monitor stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        self.logger.info("Camera monitoring loop started")

        while self.running and not self._stop_event.is_set():
            try:
                self.last_check_time = time.time()
                self.check_count += 1

                # Check all configured cameras
                self._check_all_cameras()

                # Wait for next check
                if self._stop_event.wait(self.check_interval):
                    break

            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Error in camera monitoring loop: {e}")

                # Wait a bit before retrying
                if self._stop_event.wait(min(self.check_interval, 10)):
                    break

        self.logger.info("Camera monitoring loop ended")

    def _check_all_cameras(self) -> None:
        """Check status of all configured cameras"""
        for camera_config in self.config.cameras:
            if not camera_config.enabled:
                continue

            try:
                self._check_camera_status(camera_config.name)
            except Exception as e:
                self.logger.error(f"Error checking camera {camera_config.name}: {e}")

    def _check_camera_status(self, camera_name: str) -> None:
        """Check status of a specific camera"""
        try:
            # Get current status from state manager
            current_info = self.state_manager.get_camera_status(camera_name)

            # Perform actual camera check
            status, details, device_info = self._perform_camera_check(camera_name)

            # Update state if changed
            old_status = current_info.status.value if current_info else "unknown"
            if old_status != status:
                self.state_manager.update_camera_status(name=camera_name, status=status, error=details if status == "error" else None, device_info=device_info)

                # Publish status change event
                publish_camera_status_changed(camera_name=camera_name, status=status, details=details)

                self.logger.info(f"Camera {camera_name} status changed: {old_status} -> {status}")

        except Exception as e:
            self.logger.error(f"Error checking camera {camera_name}: {e}")

            # Update to error state
            self.state_manager.update_camera_status(name=camera_name, status="error", error=str(e))

    def _perform_camera_check(self, camera_name: str) -> tuple[str, str, Optional[Dict[str, Any]]]:
        """Perform actual camera availability check"""
        try:
            # Get camera device info from camera manager
            if not self.camera_manager:
                return "error", "Camera manager not available", None

            device_info = self.camera_manager._find_camera_device(camera_name)
            if not device_info:
                return "disconnected", "Camera device not found", None

            # Check if camera is already opened by another process
            if mvsdk.CameraIsOpened(device_info):
                # Camera is opened - check if it's our recorder that's currently recording
                recorder = self.camera_manager.camera_recorders.get(camera_name)
                if recorder and recorder.hCamera and recorder.recording:
                    return "available", "Camera recording (in use by system)", self._get_device_info_dict(device_info)
                else:
                    return "busy", "Camera opened by another process", self._get_device_info_dict(device_info)

            # Try to initialize camera briefly to test availability
            try:
                # Ensure SDK is initialized
                ensure_sdk_initialized()

                # Suppress output to avoid MVCAMAPI error messages during camera testing
                with suppress_camera_errors():
                    hCamera = mvsdk.CameraInit(device_info, -1, -1)

                # Quick test - try to get one frame
                try:
                    mvsdk.CameraSetTriggerMode(hCamera, 0)
                    mvsdk.CameraPlay(hCamera)

                    # Try to capture with short timeout
                    pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 500)
                    mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)

                    # Success - camera is available
                    mvsdk.CameraUnInit(hCamera)
                    return "available", "Camera test successful", self._get_device_info_dict(device_info)

                except mvsdk.CameraException as e:
                    mvsdk.CameraUnInit(hCamera)
                    if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
                        return "available", "Camera available but slow response", self._get_device_info_dict(device_info)
                    else:
                        return "error", f"Camera test failed: {e.message}", self._get_device_info_dict(device_info)

            except mvsdk.CameraException as e:
                return "error", f"Camera initialization failed: {e.message}", self._get_device_info_dict(device_info)

        except Exception as e:
            return "error", f"Camera check failed: {str(e)}", None

    def _get_device_info_dict(self, device_info) -> Dict[str, Any]:
        """Convert device info to dictionary"""
        try:
            return {"friendly_name": device_info.GetFriendlyName(), "port_type": device_info.GetPortType(), "serial_number": getattr(device_info, "acSn", "Unknown"), "last_checked": time.time()}
        except Exception as e:
            self.logger.error(f"Error getting device info: {e}")
            return {"error": str(e)}

    def check_camera_now(self, camera_name: str) -> Dict[str, Any]:
        """Manually check a specific camera status"""
        try:
            status, details, device_info = self._perform_camera_check(camera_name)

            # Update state
            self.state_manager.update_camera_status(name=camera_name, status=status, error=details if status == "error" else None, device_info=device_info)

            return {"camera_name": camera_name, "status": status, "details": details, "device_info": device_info, "check_time": time.time()}

        except Exception as e:
            error_msg = f"Manual camera check failed: {e}"
            self.logger.error(error_msg)
            return {"camera_name": camera_name, "status": "error", "details": error_msg, "device_info": None, "check_time": time.time()}

    def check_all_cameras_now(self) -> Dict[str, Dict[str, Any]]:
        """Manually check all cameras"""
        results = {}
        for camera_config in self.config.cameras:
            if camera_config.enabled:
                results[camera_config.name] = self.check_camera_now(camera_config.name)
        return results

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        return {"running": self.running, "check_interval_seconds": self.check_interval, "total_checks": self.check_count, "error_count": self.error_count, "last_check_time": self.last_check_time, "success_rate": (self.check_count - self.error_count) / max(self.check_count, 1) * 100}

    def is_running(self) -> bool:
        """Check if monitor is running"""
        return self.running
