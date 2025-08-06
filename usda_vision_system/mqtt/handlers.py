"""
MQTT Message Handlers for the USDA Vision Camera System.

This module handles processing of MQTT messages and triggering appropriate actions.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from ..core.state_manager import StateManager, MachineState
from ..core.events import EventSystem, publish_machine_state_changed


class MQTTMessageHandler:
    """Handles MQTT messages and triggers appropriate system actions"""

    def __init__(self, state_manager: StateManager, event_system: EventSystem):
        self.state_manager = state_manager
        self.event_system = event_system
        self.logger = logging.getLogger(__name__)

        # Message processing statistics
        self.message_count = 0
        self.last_message_time: Optional[datetime] = None
        self.error_count = 0

    def handle_message(self, machine_name: str, topic: str, payload: str) -> None:
        """Handle an incoming MQTT message"""
        try:
            self.message_count += 1
            self.last_message_time = datetime.now()

            self.logger.info(f"Processing MQTT message - Machine: {machine_name}, Topic: {topic}, Payload: {payload}")

            # Normalize payload
            normalized_payload = self._normalize_payload(payload)

            # Update machine state
            state_changed = self.state_manager.update_machine_state(name=machine_name, state=normalized_payload, message=payload, topic=topic)

            # Store MQTT event in history
            self.state_manager.add_mqtt_event(machine_name=machine_name, topic=topic, payload=payload, normalized_state=normalized_payload)

            # Publish state change event if state actually changed
            if state_changed:
                publish_machine_state_changed(machine_name=machine_name, state=normalized_payload, source="mqtt_handler")

                self.logger.info(f"Machine {machine_name} state changed to: {normalized_payload}")

            # Log the message for debugging
            self._log_message_details(machine_name, topic, payload, normalized_payload)

        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error handling MQTT message for {machine_name}: {e}")

    def _normalize_payload(self, payload: str) -> str:
        """Normalize payload to standard machine states"""
        payload_lower = payload.lower().strip()

        # Map various possible payloads to standard states
        if payload_lower in ["on", "true", "1", "start", "running", "active"]:
            return "on"
        elif payload_lower in ["off", "false", "0", "stop", "stopped", "inactive"]:
            return "off"
        elif payload_lower in ["error", "fault", "alarm"]:
            return "error"
        else:
            # For unknown payloads, log and return as-is
            self.logger.warning(f"Unknown payload format: '{payload}', treating as raw state")
            return payload_lower

    def _log_message_details(self, machine_name: str, topic: str, original_payload: str, normalized_payload: str) -> None:
        """Log detailed message information"""
        self.logger.debug(f"MQTT Message Details:")
        self.logger.debug(f"  Machine: {machine_name}")
        self.logger.debug(f"  Topic: {topic}")
        self.logger.debug(f"  Original Payload: '{original_payload}'")
        self.logger.debug(f"  Normalized Payload: '{normalized_payload}'")
        self.logger.debug(f"  Timestamp: {self.last_message_time}")
        self.logger.debug(f"  Total Messages Processed: {self.message_count}")

    def get_statistics(self) -> Dict[str, any]:
        """Get message processing statistics"""
        return {"total_messages": self.message_count, "error_count": self.error_count, "last_message_time": self.last_message_time.isoformat() if self.last_message_time else None, "success_rate": (self.message_count - self.error_count) / max(self.message_count, 1) * 100}

    def reset_statistics(self) -> None:
        """Reset message processing statistics"""
        self.message_count = 0
        self.error_count = 0
        self.last_message_time = None
        self.logger.info("MQTT message handler statistics reset")


class MachineStateProcessor:
    """Processes machine state changes and determines actions"""

    def __init__(self, state_manager: StateManager, event_system: EventSystem):
        self.state_manager = state_manager
        self.event_system = event_system
        self.logger = logging.getLogger(__name__)

    def process_state_change(self, machine_name: str, old_state: str, new_state: str) -> None:
        """Process a machine state change and determine what actions to take"""
        self.logger.info(f"Processing state change for {machine_name}: {old_state} -> {new_state}")

        # Handle state transitions
        if old_state != "on" and new_state == "on":
            self._handle_machine_turned_on(machine_name)
        elif old_state == "on" and new_state != "on":
            self._handle_machine_turned_off(machine_name)
        elif new_state == "error":
            self._handle_machine_error(machine_name)

    def _handle_machine_turned_on(self, machine_name: str) -> None:
        """Handle machine turning on - should start recording"""
        self.logger.info(f"Machine {machine_name} turned ON - should start recording")

        # The actual recording start will be handled by the camera manager
        # which listens to the MACHINE_STATE_CHANGED event

        # We could add additional logic here, such as:
        # - Checking if camera is available
        # - Pre-warming camera settings
        # - Sending notifications

    def _handle_machine_turned_off(self, machine_name: str) -> None:
        """Handle machine turning off - should stop recording"""
        self.logger.info(f"Machine {machine_name} turned OFF - should stop recording")

        # The actual recording stop will be handled by the camera manager
        # which listens to the MACHINE_STATE_CHANGED event

    def _handle_machine_error(self, machine_name: str) -> None:
        """Handle machine error state"""
        self.logger.warning(f"Machine {machine_name} in ERROR state")

        # Could implement error handling logic here:
        # - Stop recording if active
        # - Send alerts
        # - Log error details
