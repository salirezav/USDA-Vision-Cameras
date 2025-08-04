#!/usr/bin/env python3
"""
Standalone Auto-Recording System for USDA Vision Cameras

This is a simplified, reliable auto-recording system that:
1. Monitors MQTT messages directly
2. Starts/stops camera recordings based on machine state
3. Works independently of the main system
4. Is easy to debug and maintain

Usage:
    sudo python -m usda_vision_system.recording.standalone_auto_recorder
"""

import json
import logging
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import paho.mqtt.client as mqtt

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from usda_vision_system.core.config import Config
from usda_vision_system.camera.recorder import CameraRecorder
from usda_vision_system.core.state_manager import StateManager
from usda_vision_system.core.events import EventSystem


class StandaloneAutoRecorder:
    """Standalone auto-recording system that monitors MQTT and controls cameras directly"""

    def __init__(self, config_path: str = "config.json", config: Optional[Config] = None):
        # Load configuration
        if config:
            self.config = config
        else:
            self.config = Config(config_path)

        # Setup logging (only if not already configured)
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.FileHandler("standalone_auto_recorder.log"), logging.StreamHandler()])
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.state_manager = StateManager()
        self.event_system = EventSystem()

        # MQTT client
        self.mqtt_client: Optional[mqtt.Client] = None

        # Camera recorders
        self.camera_recorders: Dict[str, CameraRecorder] = {}
        self.active_recordings: Dict[str, str] = {}  # camera_name -> filename

        # Machine to camera mapping
        self.machine_camera_map = self._build_machine_camera_map()

        # Threading
        self.running = False
        self._stop_event = threading.Event()

        self.logger.info("Standalone Auto-Recorder initialized")
        self.logger.info(f"Machine-Camera mapping: {self.machine_camera_map}")

    def _build_machine_camera_map(self) -> Dict[str, str]:
        """Build mapping from machine topics to camera names"""
        mapping = {}
        for camera_config in self.config.cameras:
            if camera_config.enabled and camera_config.auto_start_recording_enabled:
                machine_name = camera_config.machine_topic
                if machine_name:
                    mapping[machine_name] = camera_config.name
                    self.logger.info(f"Auto-recording enabled: {machine_name} -> {camera_config.name}")
        return mapping

    def _setup_mqtt(self) -> bool:
        """Setup MQTT client"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_message = self._on_mqtt_message
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect

            # Connect to MQTT broker
            self.logger.info(f"Connecting to MQTT broker at {self.config.mqtt.broker_host}:{self.config.mqtt.broker_port}")
            self.mqtt_client.connect(self.config.mqtt.broker_host, self.config.mqtt.broker_port, 60)

            # Start MQTT loop in background
            self.mqtt_client.loop_start()

            return True

        except Exception as e:
            self.logger.error(f"Failed to setup MQTT: {e}")
            return False

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.logger.info("Connected to MQTT broker")

            # Subscribe to machine state topics
            for machine_name in self.machine_camera_map.keys():
                if hasattr(self.config.mqtt, "topics") and self.config.mqtt.topics:
                    topic = self.config.mqtt.topics.get(machine_name)
                    if topic:
                        client.subscribe(topic)
                        self.logger.info(f"Subscribed to: {topic}")
                    else:
                        self.logger.warning(f"No MQTT topic configured for machine: {machine_name}")
                else:
                    # Fallback to default topic format
                    topic = f"vision/{machine_name}/state"
                    client.subscribe(topic)
                    self.logger.info(f"Subscribed to: {topic} (default format)")
        else:
            self.logger.error(f"Failed to connect to MQTT broker: {rc}")

    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.logger.warning(f"Disconnected from MQTT broker: {rc}")

    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8").strip().lower()

            # Extract machine name from topic (vision/{machine_name}/state)
            topic_parts = topic.split("/")
            if len(topic_parts) >= 3 and topic_parts[0] == "vision" and topic_parts[2] == "state":
                machine_name = topic_parts[1]

                self.logger.info(f"MQTT: {machine_name} -> {payload}")

                # Handle state change
                self._handle_machine_state_change(machine_name, payload)

        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")

    def _handle_machine_state_change(self, machine_name: str, state: str):
        """Handle machine state change"""
        try:
            # Check if we have a camera for this machine
            camera_name = self.machine_camera_map.get(machine_name)
            if not camera_name:
                return

            self.logger.info(f"Handling state change: {machine_name} ({camera_name}) -> {state}")

            if state == "on":
                self._start_recording(camera_name, machine_name)
            elif state == "off":
                self._stop_recording(camera_name, machine_name)

        except Exception as e:
            self.logger.error(f"Error handling machine state change: {e}")

    def _start_recording(self, camera_name: str, machine_name: str):
        """Start recording for a camera"""
        try:
            # Check if already recording
            if camera_name in self.active_recordings:
                self.logger.warning(f"Camera {camera_name} is already recording")
                return

            # Get or create camera recorder
            recorder = self._get_camera_recorder(camera_name)
            if not recorder:
                self.logger.error(f"Failed to get recorder for camera {camera_name}")
                return

            # Generate filename with timestamp and machine info
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            camera_config = self.config.get_camera_by_name(camera_name)
            video_format = camera_config.video_format if camera_config else "mp4"
            filename = f"{camera_name}_auto_{machine_name}_{timestamp}.{video_format}"

            # Start recording
            success = recorder.start_recording(filename)
            if success:
                self.active_recordings[camera_name] = filename
                self.logger.info(f"✅ Started recording: {camera_name} -> {filename}")
            else:
                self.logger.error(f"❌ Failed to start recording for camera {camera_name}")

        except Exception as e:
            self.logger.error(f"Error starting recording for {camera_name}: {e}")

    def _stop_recording(self, camera_name: str, machine_name: str):
        """Stop recording for a camera"""
        try:
            # Check if recording
            if camera_name not in self.active_recordings:
                self.logger.warning(f"Camera {camera_name} is not recording")
                return

            # Get recorder
            recorder = self._get_camera_recorder(camera_name)
            if not recorder:
                self.logger.error(f"Failed to get recorder for camera {camera_name}")
                return

            # Stop recording
            filename = self.active_recordings.pop(camera_name)
            success = recorder.stop_recording()

            if success:
                self.logger.info(f"✅ Stopped recording: {camera_name} -> {filename}")
            else:
                self.logger.error(f"❌ Failed to stop recording for camera {camera_name}")

        except Exception as e:
            self.logger.error(f"Error stopping recording for {camera_name}: {e}")

    def _get_camera_recorder(self, camera_name: str) -> Optional[CameraRecorder]:
        """Get or create camera recorder"""
        try:
            # Return existing recorder
            if camera_name in self.camera_recorders:
                return self.camera_recorders[camera_name]

            # Find camera config
            camera_config = None
            for config in self.config.cameras:
                if config.name == camera_name:
                    camera_config = config
                    break

            if not camera_config:
                self.logger.error(f"No configuration found for camera {camera_name}")
                return None

            # Find device info (simplified camera discovery)
            device_info = self._find_camera_device(camera_name)
            if not device_info:
                self.logger.error(f"No device found for camera {camera_name}")
                return None

            # Create recorder
            recorder = CameraRecorder(camera_config=camera_config, device_info=device_info, state_manager=self.state_manager, event_system=self.event_system)

            self.camera_recorders[camera_name] = recorder
            self.logger.info(f"Created recorder for camera {camera_name}")
            return recorder

        except Exception as e:
            self.logger.error(f"Error creating recorder for {camera_name}: {e}")
            return None

    def _find_camera_device(self, camera_name: str):
        """Simplified camera device discovery"""
        try:
            # Import camera SDK
            import sys
            import os

            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "camera_sdk"))
            import mvsdk

            # Initialize SDK
            mvsdk.CameraSdkInit(1)

            # Enumerate cameras
            device_list = mvsdk.CameraEnumerateDevice()

            # For now, map by index (camera1 = index 0, camera2 = index 1)
            camera_index = int(camera_name.replace("camera", "")) - 1

            if 0 <= camera_index < len(device_list):
                return device_list[camera_index]
            else:
                self.logger.error(f"Camera index {camera_index} not found (total: {len(device_list)})")
                return None

        except Exception as e:
            self.logger.error(f"Error finding camera device: {e}")
            return None

    def start(self) -> bool:
        """Start the standalone auto-recorder"""
        try:
            self.logger.info("Starting Standalone Auto-Recorder...")

            # Setup MQTT
            if not self._setup_mqtt():
                return False

            # Wait for MQTT connection
            time.sleep(2)

            self.running = True
            self.logger.info("✅ Standalone Auto-Recorder started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start auto-recorder: {e}")
            return False

    def stop(self) -> bool:
        """Stop the standalone auto-recorder"""
        try:
            self.logger.info("Stopping Standalone Auto-Recorder...")
            self.running = False
            self._stop_event.set()

            # Stop all active recordings
            for camera_name in list(self.active_recordings.keys()):
                self._stop_recording(camera_name, "system_shutdown")

            # Cleanup camera recorders
            for recorder in self.camera_recorders.values():
                try:
                    recorder.cleanup()
                except:
                    pass

            # Stop MQTT
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()

            self.logger.info("✅ Standalone Auto-Recorder stopped")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping auto-recorder: {e}")
            return False

    def run(self):
        """Run the auto-recorder (blocking)"""
        if not self.start():
            return False

        try:
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            self.logger.info("Auto-recorder running... Press Ctrl+C to stop")

            # Main loop
            while self.running and not self._stop_event.is_set():
                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            self.stop()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self._stop_event.set()


def main():
    """Main entry point"""
    recorder = StandaloneAutoRecorder()
    recorder.run()


if __name__ == "__main__":
    main()
