"""
MQTT Client for the USDA Vision Camera System.

This module provides MQTT connectivity and message handling for machine state updates.
"""

import threading
import time
import logging
from typing import Dict, Optional, Callable, List
import paho.mqtt.client as mqtt

from ..core.config import Config, MQTTConfig
from ..core.state_manager import StateManager
from ..core.events import EventSystem, EventType, publish_machine_state_changed
from .handlers import MQTTMessageHandler


class MQTTClient:
    """MQTT client for receiving machine state updates"""
    
    def __init__(self, config: Config, state_manager: StateManager, event_system: EventSystem):
        self.config = config
        self.mqtt_config = config.mqtt
        self.state_manager = state_manager
        self.event_system = event_system
        self.logger = logging.getLogger(__name__)
        
        # MQTT client
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.running = False
        
        # Threading
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Message handler
        self.message_handler = MQTTMessageHandler(state_manager, event_system)
        
        # Connection retry settings
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_attempts = 10
        
        # Topic mapping (topic -> machine_name)
        self.topic_to_machine = {
            topic: machine_name 
            for machine_name, topic in self.mqtt_config.topics.items()
        }
    
    def start(self) -> bool:
        """Start the MQTT client in a separate thread"""
        if self.running:
            self.logger.warning("MQTT client is already running")
            return True
        
        self.logger.info("Starting MQTT client...")
        self.running = True
        self._stop_event.clear()
        
        # Start in separate thread
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        # Wait a moment to see if connection succeeds
        time.sleep(2)
        return self.connected
    
    def stop(self) -> None:
        """Stop the MQTT client"""
        if not self.running:
            return
        
        self.logger.info("Stopping MQTT client...")
        self.running = False
        self._stop_event.set()
        
        if self.client and self.connected:
            self.client.disconnect()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        
        self.logger.info("MQTT client stopped")
    
    def _run_loop(self) -> None:
        """Main MQTT client loop"""
        reconnect_attempts = 0
        
        while self.running and not self._stop_event.is_set():
            try:
                if not self.connected:
                    if self._connect():
                        reconnect_attempts = 0
                        self._subscribe_to_topics()
                    else:
                        reconnect_attempts += 1
                        if reconnect_attempts >= self.max_reconnect_attempts:
                            self.logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
                            break
                        
                        self.logger.warning(f"Reconnection attempt {reconnect_attempts}/{self.max_reconnect_attempts} in {self.reconnect_delay}s")
                        if self._stop_event.wait(self.reconnect_delay):
                            break
                        continue
                
                # Process MQTT messages
                if self.client:
                    self.client.loop(timeout=1.0)
                
                # Small delay to prevent busy waiting
                if self._stop_event.wait(0.1):
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in MQTT loop: {e}")
                self.connected = False
                if self._stop_event.wait(self.reconnect_delay):
                    break
        
        self.running = False
        self.logger.info("MQTT client loop ended")
    
    def _connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            # Create new client instance
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Set authentication if provided
            if self.mqtt_config.username and self.mqtt_config.password:
                self.client.username_pw_set(
                    self.mqtt_config.username, 
                    self.mqtt_config.password
                )
            
            # Connect to broker
            self.logger.info(f"Connecting to MQTT broker at {self.mqtt_config.broker_host}:{self.mqtt_config.broker_port}")
            self.client.connect(
                self.mqtt_config.broker_host, 
                self.mqtt_config.broker_port, 
                60
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def _subscribe_to_topics(self) -> None:
        """Subscribe to all configured topics"""
        if not self.client or not self.connected:
            return
        
        for machine_name, topic in self.mqtt_config.topics.items():
            try:
                result, mid = self.client.subscribe(topic)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    self.logger.info(f"Subscribed to topic: {topic} (machine: {machine_name})")
                else:
                    self.logger.error(f"Failed to subscribe to topic: {topic}")
            except Exception as e:
                self.logger.error(f"Error subscribing to topic {topic}: {e}")
    
    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Callback for when the client connects to the broker"""
        if rc == 0:
            self.connected = True
            self.state_manager.set_mqtt_connected(True)
            self.event_system.publish(EventType.MQTT_CONNECTED, "mqtt_client")
            self.logger.info("Successfully connected to MQTT broker")
        else:
            self.connected = False
            self.logger.error(f"Failed to connect to MQTT broker, return code {rc}")
    
    def _on_disconnect(self, client, userdata, rc) -> None:
        """Callback for when the client disconnects from the broker"""
        self.connected = False
        self.state_manager.set_mqtt_connected(False)
        self.event_system.publish(EventType.MQTT_DISCONNECTED, "mqtt_client")
        
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection (rc: {rc})")
        else:
            self.logger.info("MQTT client disconnected")
    
    def _on_message(self, client, userdata, msg) -> None:
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8').strip()
            
            self.logger.debug(f"MQTT message received - Topic: {topic}, Payload: {payload}")
            
            # Update MQTT activity
            self.state_manager.update_mqtt_activity()
            
            # Get machine name from topic
            machine_name = self.topic_to_machine.get(topic)
            if not machine_name:
                self.logger.warning(f"Unknown topic: {topic}")
                return
            
            # Handle the message
            self.message_handler.handle_message(machine_name, topic, payload)
            
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")
    
    def publish_message(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> bool:
        """Publish a message to MQTT broker"""
        if not self.client or not self.connected:
            self.logger.warning("Cannot publish: MQTT client not connected")
            return False
        
        try:
            result = self.client.publish(topic, payload, qos, retain)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published message to {topic}: {payload}")
                return True
            else:
                self.logger.error(f"Failed to publish message to {topic}")
                return False
        except Exception as e:
            self.logger.error(f"Error publishing message: {e}")
            return False
    
    def get_status(self) -> Dict[str, any]:
        """Get MQTT client status"""
        return {
            "connected": self.connected,
            "running": self.running,
            "broker_host": self.mqtt_config.broker_host,
            "broker_port": self.mqtt_config.broker_port,
            "subscribed_topics": list(self.mqtt_config.topics.values()),
            "topic_mappings": self.topic_to_machine
        }
    
    def is_connected(self) -> bool:
        """Check if MQTT client is connected"""
        return self.connected
    
    def is_running(self) -> bool:
        """Check if MQTT client is running"""
        return self.running
