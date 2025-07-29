"""
Auto-Recording Manager for the USDA Vision Camera System.

This module manages automatic recording start/stop based on machine state changes
received via MQTT. It includes retry logic for failed recording attempts and
tracks auto-recording status for each camera.
"""

import threading
import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

from ..core.config import Config, CameraConfig
from ..core.state_manager import StateManager, MachineState
from ..core.events import EventSystem, EventType, Event
from ..core.timezone_utils import format_filename_timestamp


class AutoRecordingManager:
    """Manages automatic recording based on machine state changes"""

    def __init__(self, config: Config, state_manager: StateManager, event_system: EventSystem, camera_manager):
        self.config = config
        self.state_manager = state_manager
        self.event_system = event_system
        self.camera_manager = camera_manager
        self.logger = logging.getLogger(__name__)

        # Threading
        self.running = False
        self._retry_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Track retry attempts for each camera
        self._retry_queue: Dict[str, Dict[str, Any]] = {}  # camera_name -> retry_info
        self._retry_lock = threading.RLock()

        # Subscribe to machine state change events
        self.event_system.subscribe(EventType.MACHINE_STATE_CHANGED, self._on_machine_state_changed)

    def start(self) -> bool:
        """Start the auto-recording manager"""
        if self.running:
            self.logger.warning("Auto-recording manager is already running")
            return True

        if not self.config.system.auto_recording_enabled:
            self.logger.info("Auto-recording is disabled in system configuration")
            return True

        self.logger.info("Starting auto-recording manager...")
        self.running = True
        self._stop_event.clear()

        # Initialize camera auto-recording status
        self._initialize_camera_status()

        # Start retry thread
        self._retry_thread = threading.Thread(target=self._retry_loop, daemon=True)
        self._retry_thread.start()

        self.logger.info("Auto-recording manager started successfully")
        return True

    def stop(self) -> None:
        """Stop the auto-recording manager"""
        if not self.running:
            return

        self.logger.info("Stopping auto-recording manager...")
        self.running = False
        self._stop_event.set()

        # Wait for retry thread to finish
        if self._retry_thread and self._retry_thread.is_alive():
            self._retry_thread.join(timeout=5)

        self.logger.info("Auto-recording manager stopped")

    def _initialize_camera_status(self) -> None:
        """Initialize auto-recording status for all cameras"""
        for camera_config in self.config.cameras:
            if camera_config.enabled and camera_config.auto_start_recording_enabled:
                # Update camera status in state manager
                camera_info = self.state_manager.get_camera_status(camera_config.name)
                if camera_info:
                    camera_info.auto_recording_enabled = True
                    self.logger.info(f"Auto-recording enabled for camera {camera_config.name}")
                else:
                    # Create camera info if it doesn't exist
                    self.state_manager.update_camera_status(camera_config.name, "unknown")
                    camera_info = self.state_manager.get_camera_status(camera_config.name)
                    if camera_info:
                        camera_info.auto_recording_enabled = True
                        self.logger.info(f"Auto-recording enabled for camera {camera_config.name}")

    def _on_machine_state_changed(self, event: Event) -> None:
        """Handle machine state change events"""
        try:
            machine_name = event.data.get("machine_name")
            new_state = event.data.get("state")

            if not machine_name or not new_state:
                self.logger.warning(f"Invalid event data - machine_name: {machine_name}, state: {new_state}")
                return

            self.logger.info(f"Machine state changed: {machine_name} -> {new_state}")

            # Find cameras associated with this machine
            associated_cameras = self._get_cameras_for_machine(machine_name)

            for camera_config in associated_cameras:
                if not camera_config.enabled or not camera_config.auto_start_recording_enabled:
                    self.logger.debug(f"Skipping camera {camera_config.name} - not enabled or auto recording disabled")
                    continue

                if new_state.lower() == "on":
                    self._handle_machine_on(camera_config)
                elif new_state.lower() == "off":
                    self._handle_machine_off(camera_config)

        except Exception as e:
            self.logger.error(f"Error handling machine state change: {e}")

    def _get_cameras_for_machine(self, machine_name: str) -> list[CameraConfig]:
        """Get all cameras associated with a machine topic"""
        associated_cameras = []

        # Map machine names to topics
        machine_topic_map = {"vibratory_conveyor": "vibratory_conveyor", "blower_separator": "blower_separator"}

        machine_topic = machine_topic_map.get(machine_name)
        if not machine_topic:
            return associated_cameras

        for camera_config in self.config.cameras:
            if camera_config.machine_topic == machine_topic:
                associated_cameras.append(camera_config)

        return associated_cameras

    def _handle_machine_on(self, camera_config: CameraConfig) -> None:
        """Handle machine turning on - start recording"""
        camera_name = camera_config.name

        # Check if camera is already recording
        camera_info = self.state_manager.get_camera_status(camera_name)
        if camera_info and camera_info.is_recording:
            self.logger.info(f"Camera {camera_name} is already recording, skipping auto-start")
            return

        self.logger.info(f"Machine turned ON - attempting to start recording for camera {camera_name}")

        # Update auto-recording status
        if camera_info:
            camera_info.auto_recording_active = True
            camera_info.auto_recording_last_attempt = datetime.now()
        else:
            # Create camera info if it doesn't exist
            self.state_manager.update_camera_status(camera_name, "unknown")
            camera_info = self.state_manager.get_camera_status(camera_name)
            if camera_info:
                camera_info.auto_recording_active = True
                camera_info.auto_recording_last_attempt = datetime.now()

        # Attempt to start recording
        success = self._start_recording_for_camera(camera_config)

        if not success:
            # Add to retry queue
            self._add_to_retry_queue(camera_config, "start")

    def _handle_machine_off(self, camera_config: CameraConfig) -> None:
        """Handle machine turning off - stop recording"""
        camera_name = camera_config.name

        self.logger.info(f"Machine turned OFF - attempting to stop recording for camera {camera_name}")

        # Update auto-recording status
        camera_info = self.state_manager.get_camera_status(camera_name)
        if camera_info:
            camera_info.auto_recording_active = False

        # Remove from retry queue if present
        with self._retry_lock:
            if camera_name in self._retry_queue:
                del self._retry_queue[camera_name]

        # Attempt to stop recording
        self._stop_recording_for_camera(camera_config)

    def _start_recording_for_camera(self, camera_config: CameraConfig) -> bool:
        """Start recording for a specific camera using its default configuration"""
        try:
            camera_name = camera_config.name

            # Generate filename with timestamp and machine info
            timestamp = format_filename_timestamp()
            machine_name = camera_config.machine_topic.replace("_", "-")
            filename = f"{camera_name}_auto_{machine_name}_{timestamp}.avi"

            # Use camera manager to start recording with the camera's default configuration
            # Pass the camera's configured settings from config.json
            success = self.camera_manager.manual_start_recording(camera_name=camera_name, filename=filename, exposure_ms=camera_config.exposure_ms, gain=camera_config.gain, fps=camera_config.target_fps)

            if success:
                self.logger.info(f"Successfully started auto-recording for camera {camera_name}: {filename}")
                self.logger.info(f"Using camera settings - Exposure: {camera_config.exposure_ms}ms, Gain: {camera_config.gain}, FPS: {camera_config.target_fps}")

                # Update status
                camera_info = self.state_manager.get_camera_status(camera_name)
                if camera_info:
                    camera_info.auto_recording_failure_count = 0
                    camera_info.auto_recording_last_error = None

                return True
            else:
                self.logger.error(f"Failed to start auto-recording for camera {camera_name}")
                return False

        except Exception as e:
            self.logger.error(f"Error starting auto-recording for camera {camera_config.name}: {e}")

            # Update error status
            camera_info = self.state_manager.get_camera_status(camera_config.name)
            if camera_info:
                camera_info.auto_recording_last_error = str(e)

            return False

    def _stop_recording_for_camera(self, camera_config: CameraConfig) -> bool:
        """Stop recording for a specific camera"""
        try:
            camera_name = camera_config.name

            # Use camera manager to stop recording
            success = self.camera_manager.manual_stop_recording(camera_name)

            if success:
                self.logger.info(f"Successfully stopped auto-recording for camera {camera_name}")
                return True
            else:
                self.logger.warning(f"Failed to stop auto-recording for camera {camera_name} (may not have been recording)")
                return False

        except Exception as e:
            self.logger.error(f"Error stopping auto-recording for camera {camera_config.name}: {e}")
            return False

    def _add_to_retry_queue(self, camera_config: CameraConfig, action: str) -> None:
        """Add a camera to the retry queue"""
        with self._retry_lock:
            camera_name = camera_config.name

            retry_info = {"camera_config": camera_config, "action": action, "attempt_count": 0, "next_retry_time": datetime.now() + timedelta(seconds=camera_config.auto_recording_retry_delay_seconds), "max_retries": camera_config.auto_recording_max_retries}

            self._retry_queue[camera_name] = retry_info
            self.logger.info(f"Added camera {camera_name} to retry queue for {action} (max retries: {retry_info['max_retries']})")

    def _retry_loop(self) -> None:
        """Background thread to handle retry attempts"""
        while self.running and not self._stop_event.is_set():
            try:
                current_time = datetime.now()
                cameras_to_retry = []

                # Find cameras ready for retry
                with self._retry_lock:
                    for camera_name, retry_info in list(self._retry_queue.items()):
                        if current_time >= retry_info["next_retry_time"]:
                            cameras_to_retry.append((camera_name, retry_info))

                # Process retries
                for camera_name, retry_info in cameras_to_retry:
                    self._process_retry(camera_name, retry_info)

                # Sleep for a short interval
                self._stop_event.wait(1)

            except Exception as e:
                self.logger.error(f"Error in retry loop: {e}")
                self._stop_event.wait(5)

    def _process_retry(self, camera_name: str, retry_info: Dict[str, Any]) -> None:
        """Process a retry attempt for a camera"""
        try:
            retry_info["attempt_count"] += 1
            camera_config = retry_info["camera_config"]
            action = retry_info["action"]

            self.logger.info(f"Retry attempt {retry_info['attempt_count']}/{retry_info['max_retries']} for camera {camera_name} ({action})")

            # Update camera status
            camera_info = self.state_manager.get_camera_status(camera_name)
            if camera_info:
                camera_info.auto_recording_last_attempt = datetime.now()
                camera_info.auto_recording_failure_count = retry_info["attempt_count"]

            # Attempt the action
            success = False
            if action == "start":
                success = self._start_recording_for_camera(camera_config)

            if success:
                # Success - remove from retry queue
                with self._retry_lock:
                    if camera_name in self._retry_queue:
                        del self._retry_queue[camera_name]
                self.logger.info(f"Retry successful for camera {camera_name}")
            else:
                # Failed - check if we should retry again
                if retry_info["attempt_count"] >= retry_info["max_retries"]:
                    # Max retries reached
                    with self._retry_lock:
                        if camera_name in self._retry_queue:
                            del self._retry_queue[camera_name]

                    error_msg = f"Max retry attempts ({retry_info['max_retries']}) reached for camera {camera_name}"
                    self.logger.error(error_msg)

                    # Update camera status
                    if camera_info:
                        camera_info.auto_recording_last_error = error_msg
                        camera_info.auto_recording_active = False
                else:
                    # Schedule next retry
                    retry_info["next_retry_time"] = datetime.now() + timedelta(seconds=camera_config.auto_recording_retry_delay_seconds)
                    self.logger.info(f"Scheduling next retry for camera {camera_name} in {camera_config.auto_recording_retry_delay_seconds} seconds")

        except Exception as e:
            self.logger.error(f"Error processing retry for camera {camera_name}: {e}")

            # Remove from retry queue on error
            with self._retry_lock:
                if camera_name in self._retry_queue:
                    del self._retry_queue[camera_name]

    def get_status(self) -> Dict[str, Any]:
        """Get auto-recording manager status"""
        with self._retry_lock:
            retry_queue_status = {camera_name: {"action": info["action"], "attempt_count": info["attempt_count"], "max_retries": info["max_retries"], "next_retry_time": info["next_retry_time"].isoformat()} for camera_name, info in self._retry_queue.items()}

        return {"running": self.running, "auto_recording_enabled": self.config.system.auto_recording_enabled, "retry_queue": retry_queue_status, "enabled_cameras": [camera.name for camera in self.config.cameras if camera.enabled and camera.auto_start_recording_enabled]}
