"""
Camera Manager for the USDA Vision Camera System.

This module manages GigE camera discovery, initialization, and coordination
with the recording system based on machine state changes.
"""

import sys
import os
import threading
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Add camera SDK to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "camera_sdk"))
import mvsdk

from ..core.config import Config, CameraConfig
from ..core.state_manager import StateManager, CameraStatus
from ..core.events import EventSystem, EventType, Event, publish_camera_status_changed
from ..core.timezone_utils import format_filename_timestamp
from .recorder import CameraRecorder
from .monitor import CameraMonitor
from .streamer import CameraStreamer
from .sdk_config import initialize_sdk_with_suppression


class CameraManager:
    """Manages all cameras in the system"""

    def __init__(self, config: Config, state_manager: StateManager, event_system: EventSystem):
        self.config = config
        self.state_manager = state_manager
        self.event_system = event_system
        self.logger = logging.getLogger(__name__)

        # Initialize SDK early to suppress error messages
        initialize_sdk_with_suppression()

        # Camera management
        self.available_cameras: List[Any] = []  # mvsdk camera device info
        self.camera_recorders: Dict[str, CameraRecorder] = {}  # camera_name -> recorder
        self.camera_streamers: Dict[str, CameraStreamer] = {}  # camera_name -> streamer
        self.camera_monitor: Optional[CameraMonitor] = None

        # Threading
        self._lock = threading.RLock()
        self.running = False

        # Subscribe to machine state changes
        self.event_system.subscribe(EventType.MACHINE_STATE_CHANGED, self._on_machine_state_changed)

        # Initialize camera discovery
        self._discover_cameras()

        # Create camera monitor
        self.camera_monitor = CameraMonitor(config=config, state_manager=state_manager, event_system=event_system, camera_manager=self)

    def start(self) -> bool:
        """Start the camera manager"""
        if self.running:
            self.logger.warning("Camera manager is already running")
            return True

        self.logger.info("Starting camera manager...")
        self.running = True

        # Start camera monitor
        if self.camera_monitor:
            self.camera_monitor.start()

        # Initialize camera recorders
        self._initialize_recorders()

        # Initialize camera streamers
        self._initialize_streamers()

        self.logger.info("Camera manager started successfully")
        return True

    def stop(self) -> None:
        """Stop the camera manager"""
        if not self.running:
            return

        self.logger.info("Stopping camera manager...")
        self.running = False

        # Stop camera monitor
        if self.camera_monitor:
            self.camera_monitor.stop()

        # Stop all active recordings
        with self._lock:
            for recorder in self.camera_recorders.values():
                if recorder.is_recording():
                    recorder.stop_recording()
                recorder.cleanup()

        # Stop all active streaming
        with self._lock:
            for streamer in self.camera_streamers.values():
                if streamer.is_streaming():
                    streamer.stop_streaming()

        self.logger.info("Camera manager stopped")

    def _discover_cameras(self) -> None:
        """Discover available GigE cameras"""
        try:
            self.logger.info("Discovering GigE cameras...")

            # Enumerate cameras using mvsdk
            device_list = mvsdk.CameraEnumerateDevice()
            self.available_cameras = device_list

            self.logger.info(f"Found {len(device_list)} camera(s)")

            for i, dev_info in enumerate(device_list):
                try:
                    name = dev_info.GetFriendlyName()
                    port_type = dev_info.GetPortType()
                    serial = getattr(dev_info, "acSn", "Unknown")

                    self.logger.info(f"  Camera {i}: {name} ({port_type}) - Serial: {serial}")

                    # Update state manager with discovered camera
                    camera_name = f"camera{i+1}"  # Default naming
                    self.state_manager.update_camera_status(name=camera_name, status="available", device_info={"friendly_name": name, "port_type": port_type, "serial_number": serial, "device_index": i})

                except Exception as e:
                    self.logger.error(f"Error processing camera {i}: {e}")

        except Exception as e:
            self.logger.error(f"Error discovering cameras: {e}")
            self.available_cameras = []

    def _initialize_recorders(self) -> None:
        """Initialize camera recorders for configured cameras"""
        with self._lock:
            for camera_config in self.config.cameras:
                if not camera_config.enabled:
                    continue

                try:
                    # Find matching physical camera
                    device_info = self._find_camera_device(camera_config.name)
                    if device_info is None:
                        self.logger.warning(f"No physical camera found for configured camera: {camera_config.name}")
                        # Update state to indicate camera is not available
                        self.state_manager.update_camera_status(name=camera_config.name, status="not_found", device_info=None)
                        continue

                    # Create recorder (uses lazy initialization - camera will be initialized when recording starts)
                    recorder = CameraRecorder(camera_config=camera_config, device_info=device_info, state_manager=self.state_manager, event_system=self.event_system)

                    # Add recorder to the list (camera will be initialized lazily when needed)
                    self.camera_recorders[camera_config.name] = recorder
                    self.logger.info(f"Successfully created recorder for camera: {camera_config.name} (lazy initialization)")

                except Exception as e:
                    self.logger.error(f"Error initializing recorder for {camera_config.name}: {e}")
                    # Update state to indicate error
                    self.state_manager.update_camera_status(name=camera_config.name, status="error", device_info={"error": str(e)})

    def _find_camera_device(self, camera_name: str) -> Optional[Any]:
        """Find physical camera device for a configured camera"""
        # For now, use simple mapping: camera1 -> device 0, camera2 -> device 1, etc.
        # This could be enhanced to use serial numbers or other identifiers

        camera_index_map = {"camera1": 0, "camera2": 1, "camera3": 2, "camera4": 3}

        device_index = camera_index_map.get(camera_name)
        if device_index is not None and device_index < len(self.available_cameras):
            return self.available_cameras[device_index]

        return None

    def _on_machine_state_changed(self, event: Event) -> None:
        """Handle machine state change events"""
        try:
            machine_name = event.data.get("machine_name")
            new_state = event.data.get("state")

            if not machine_name or not new_state:
                return

            self.logger.info(f"Handling machine state change: {machine_name} -> {new_state}")

            # Find camera associated with this machine
            camera_config = None
            for config in self.config.cameras:
                if config.machine_topic == machine_name:
                    camera_config = config
                    break

            if not camera_config:
                self.logger.warning(f"No camera configured for machine: {machine_name}")
                return

            # Get the recorder for this camera
            recorder = self.camera_recorders.get(camera_config.name)
            if not recorder:
                self.logger.warning(f"No recorder found for camera: {camera_config.name}")
                return

            # Handle state change
            if new_state == "on":
                self._start_recording(camera_config.name, recorder)
            elif new_state in ["off", "error"]:
                self._stop_recording(camera_config.name, recorder)

        except Exception as e:
            self.logger.error(f"Error handling machine state change: {e}")

    def _start_recording(self, camera_name: str, recorder: CameraRecorder) -> None:
        """Start recording for a camera"""
        try:
            if recorder.is_recording():
                self.logger.info(f"Camera {camera_name} is already recording")
                return

            # Generate filename with Atlanta timezone timestamp
            timestamp = format_filename_timestamp()
            camera_config = self.config.get_camera_by_name(camera_name)
            video_format = camera_config.video_format if camera_config else "mp4"
            filename = f"{camera_name}_recording_{timestamp}.{video_format}"

            # Start recording
            success = recorder.start_recording(filename)
            if success:
                self.logger.info(f"Started recording for camera {camera_name}: {filename}")
            else:
                self.logger.error(f"Failed to start recording for camera {camera_name}")

        except Exception as e:
            self.logger.error(f"Error starting recording for {camera_name}: {e}")

    def _stop_recording(self, camera_name: str, recorder: CameraRecorder) -> None:
        """Stop recording for a camera"""
        try:
            if not recorder.is_recording():
                self.logger.info(f"Camera {camera_name} is not recording")
                return

            # Stop recording
            success = recorder.stop_recording()
            if success:
                self.logger.info(f"Stopped recording for camera {camera_name}")
            else:
                self.logger.error(f"Failed to stop recording for camera {camera_name}")

        except Exception as e:
            self.logger.error(f"Error stopping recording for {camera_name}: {e}")

    def get_camera_status(self, camera_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific camera"""
        recorder = self.camera_recorders.get(camera_name)
        if not recorder:
            return None

        return recorder.get_status()

    def get_all_camera_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all cameras"""
        status = {}
        with self._lock:
            for camera_name, recorder in self.camera_recorders.items():
                status[camera_name] = recorder.get_status()
        return status

    def manual_start_recording(self, camera_name: str, filename: Optional[str] = None, exposure_ms: Optional[float] = None, gain: Optional[float] = None, fps: Optional[float] = None) -> bool:
        """Manually start recording for a camera with optional camera settings"""
        recorder = self.camera_recorders.get(camera_name)
        if not recorder:
            self.logger.error(f"Camera not found: {camera_name}")
            return False

        # Update camera settings if provided
        if exposure_ms is not None or gain is not None or fps is not None:
            settings_updated = recorder.update_camera_settings(exposure_ms=exposure_ms, gain=gain, target_fps=fps)
            if not settings_updated:
                self.logger.warning(f"Failed to update camera settings for {camera_name}")

        # Generate filename with datetime prefix
        timestamp = format_filename_timestamp()
        camera_config = self.config.get_camera_by_name(camera_name)
        video_format = camera_config.video_format if camera_config else "mp4"

        if filename:
            # Always prepend datetime to the provided filename
            filename = f"{timestamp}_{filename}"
        else:
            filename = f"{camera_name}_manual_{timestamp}.{video_format}"

        return recorder.start_recording(filename)

    def manual_stop_recording(self, camera_name: str) -> bool:
        """Manually stop recording for a camera"""
        recorder = self.camera_recorders.get(camera_name)
        if not recorder:
            self.logger.error(f"Camera not found: {camera_name}")
            return False

        return recorder.stop_recording()

    def get_available_cameras(self) -> List[Dict[str, Any]]:
        """Get list of available physical cameras"""
        cameras = []
        for i, dev_info in enumerate(self.available_cameras):
            try:
                cameras.append({"index": i, "name": dev_info.GetFriendlyName(), "port_type": dev_info.GetPortType(), "serial_number": getattr(dev_info, "acSn", "Unknown")})
            except Exception as e:
                self.logger.error(f"Error getting info for camera {i}: {e}")

        return cameras

    def refresh_camera_discovery(self) -> int:
        """Refresh camera discovery and return number of cameras found"""
        self._discover_cameras()
        return len(self.available_cameras)

    def is_running(self) -> bool:
        """Check if camera manager is running"""
        return self.running

    def test_camera_connection(self, camera_name: str) -> bool:
        """Test connection for a specific camera"""
        recorder = self.camera_recorders.get(camera_name)
        if not recorder:
            self.logger.error(f"Camera not found: {camera_name}")
            return False

        return recorder.test_connection()

    def reconnect_camera(self, camera_name: str) -> bool:
        """Attempt to reconnect a specific camera"""
        recorder = self.camera_recorders.get(camera_name)
        if not recorder:
            self.logger.error(f"Camera not found: {camera_name}")
            return False

        success = recorder.reconnect()

        # Update camera status based on result
        if success:
            self.state_manager.update_camera_status(name=camera_name, status="connected", error=None)
        else:
            self.state_manager.update_camera_status(name=camera_name, status="connection_failed", error="Reconnection failed")

        return success

    def restart_camera_grab(self, camera_name: str) -> bool:
        """Restart grab process for a specific camera"""
        recorder = self.camera_recorders.get(camera_name)
        if not recorder:
            self.logger.error(f"Camera not found: {camera_name}")
            return False

        success = recorder.restart_grab()

        # Update camera status based on result
        if success:
            self.state_manager.update_camera_status(name=camera_name, status="connected", error=None)
        else:
            self.state_manager.update_camera_status(name=camera_name, status="grab_failed", error="Grab restart failed")

        return success

    def reset_camera_timestamp(self, camera_name: str) -> bool:
        """Reset timestamp for a specific camera"""
        recorder = self.camera_recorders.get(camera_name)
        if not recorder:
            self.logger.error(f"Camera not found: {camera_name}")
            return False

        return recorder.reset_timestamp()

    def full_reset_camera(self, camera_name: str) -> bool:
        """Perform full reset for a specific camera"""
        recorder = self.camera_recorders.get(camera_name)
        if not recorder:
            self.logger.error(f"Camera not found: {camera_name}")
            return False

        success = recorder.full_reset()

        # Update camera status based on result
        if success:
            self.state_manager.update_camera_status(name=camera_name, status="connected", error=None)
        else:
            self.state_manager.update_camera_status(name=camera_name, status="reset_failed", error="Full reset failed")

        return success

    def reinitialize_failed_camera(self, camera_name: str) -> bool:
        """Attempt to reinitialize a camera that failed to initialize"""
        with self._lock:
            # Find the camera config
            camera_config = None
            for config in self.config.cameras:
                if config.name == camera_name:
                    camera_config = config
                    break

            if not camera_config:
                self.logger.error(f"No configuration found for camera: {camera_name}")
                return False

            if not camera_config.enabled:
                self.logger.error(f"Camera {camera_name} is disabled in configuration")
                return False

            try:
                # Remove existing recorder if any
                if camera_name in self.camera_recorders:
                    old_recorder = self.camera_recorders[camera_name]
                    try:
                        old_recorder._cleanup_camera()
                    except:
                        pass  # Ignore cleanup errors
                    del self.camera_recorders[camera_name]

                # Find matching physical camera
                device_info = self._find_camera_device(camera_name)
                if device_info is None:
                    self.logger.warning(f"No physical camera found for configured camera: {camera_name}")
                    self.state_manager.update_camera_status(name=camera_name, status="not_found", device_info=None)
                    return False

                # Create new recorder (uses lazy initialization)
                recorder = CameraRecorder(camera_config=camera_config, device_info=device_info, state_manager=self.state_manager, event_system=self.event_system)

                # Success - add to recorders (camera will be initialized lazily when needed)
                self.camera_recorders[camera_name] = recorder
                self.state_manager.update_camera_status(name=camera_name, status="connected", error=None)

                self.logger.info(f"Successfully reinitialized camera recorder: {camera_name} (lazy initialization)")
                return True

            except Exception as e:
                self.logger.error(f"Error reinitializing camera {camera_name}: {e}")
                self.state_manager.update_camera_status(name=camera_name, status="error", device_info={"error": str(e)})
                return False

    def _initialize_streamers(self) -> None:
        """Initialize camera streamers for configured cameras"""
        with self._lock:
            for camera_config in self.config.cameras:
                if not camera_config.enabled:
                    continue

                try:
                    # Find matching physical camera
                    device_info = self._find_camera_device(camera_config.name)
                    if device_info is None:
                        self.logger.warning(f"No physical camera found for streaming: {camera_config.name}")
                        continue

                    # Create streamer
                    streamer = CameraStreamer(camera_config=camera_config, device_info=device_info, state_manager=self.state_manager, event_system=self.event_system)

                    # Add streamer to the list
                    self.camera_streamers[camera_config.name] = streamer
                    self.logger.info(f"Successfully created streamer for camera: {camera_config.name}")

                except Exception as e:
                    self.logger.error(f"Error initializing streamer for {camera_config.name}: {e}")

    def get_camera_streamer(self, camera_name: str) -> Optional[CameraStreamer]:
        """Get camera streamer for a specific camera"""
        return self.camera_streamers.get(camera_name)

    def start_camera_streaming(self, camera_name: str) -> bool:
        """Start streaming for a specific camera"""
        streamer = self.camera_streamers.get(camera_name)
        if not streamer:
            self.logger.error(f"Camera streamer not found: {camera_name}")
            return False

        return streamer.start_streaming()

    def stop_camera_streaming(self, camera_name: str) -> bool:
        """Stop streaming for a specific camera"""
        streamer = self.camera_streamers.get(camera_name)
        if not streamer:
            self.logger.error(f"Camera streamer not found: {camera_name}")
            return False

        return streamer.stop_streaming()

    def is_camera_streaming(self, camera_name: str) -> bool:
        """Check if a camera is currently streaming"""
        streamer = self.camera_streamers.get(camera_name)
        if not streamer:
            return False

        return streamer.is_streaming()

    def get_camera_config(self, camera_name: str) -> Optional[CameraConfig]:
        """Get camera configuration"""
        return self.config.get_camera_by_name(camera_name)

    def update_camera_config(self, camera_name: str, **kwargs) -> bool:
        """Update camera configuration and save to config file"""
        try:
            # Update the configuration
            success = self.config.update_camera_config(camera_name, **kwargs)
            if success:
                self.logger.info(f"Updated configuration for camera {camera_name}: {kwargs}")
                return True
            else:
                self.logger.error(f"Failed to update configuration for camera {camera_name}")
                return False
        except Exception as e:
            self.logger.error(f"Error updating camera configuration: {e}")
            return False

    def apply_camera_config(self, camera_name: str) -> bool:
        """Apply current configuration to active camera (requires camera restart)"""
        try:
            # Get the recorder for this camera
            recorder = self.camera_recorders.get(camera_name)
            if not recorder:
                self.logger.error(f"Camera recorder not found: {camera_name}")
                return False

            # Stop recording if active
            was_recording = recorder.is_recording()
            if was_recording:
                recorder.stop_recording()

            # Reinitialize the camera with new settings
            success = self.reinitialize_failed_camera(camera_name)

            if success:
                self.logger.info(f"Successfully applied configuration to camera {camera_name}")
                return True
            else:
                self.logger.error(f"Failed to apply configuration to camera {camera_name}")
                return False

        except Exception as e:
            self.logger.error(f"Error applying camera configuration: {e}")
            return False
