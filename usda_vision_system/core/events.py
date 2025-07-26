"""
Event system for the USDA Vision Camera System.

This module provides a thread-safe event system for communication between
different components of the system (MQTT, cameras, recording, etc.).
"""

import threading
import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """Event types for the system"""
    MACHINE_STATE_CHANGED = "machine_state_changed"
    CAMERA_STATUS_CHANGED = "camera_status_changed"
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    RECORDING_ERROR = "recording_error"
    MQTT_CONNECTED = "mqtt_connected"
    MQTT_DISCONNECTED = "mqtt_disconnected"
    SYSTEM_SHUTDOWN = "system_shutdown"


@dataclass
class Event:
    """Event data structure"""
    event_type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    
    def __post_init__(self):
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.now()


class EventSystem:
    """Thread-safe event system for inter-component communication"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._lock = threading.RLock()
        self._event_history: List[Event] = []
        self._max_history = 1000  # Keep last 1000 events
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Subscribe to an event type"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                self.logger.debug(f"Subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type"""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                    self.logger.debug(f"Unsubscribed from {event_type.value}")
                except ValueError:
                    pass  # Callback wasn't subscribed
    
    def publish(self, event_type: EventType, source: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publish an event"""
        if data is None:
            data = {}
        
        event = Event(
            event_type=event_type,
            source=source,
            data=data,
            timestamp=datetime.now()
        )
        
        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
        
        # Notify subscribers
        self._notify_subscribers(event)
    
    def _notify_subscribers(self, event: Event) -> None:
        """Notify all subscribers of an event"""
        with self._lock:
            subscribers = self._subscribers.get(event.event_type, []).copy()
        
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in event callback for {event.event_type.value}: {e}")
    
    def get_recent_events(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """Get recent events, optionally filtered by type"""
        with self._lock:
            events = self._event_history.copy()
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:] if limit else events
    
    def clear_history(self) -> None:
        """Clear event history"""
        with self._lock:
            self._event_history.clear()
            self.logger.info("Event history cleared")
    
    def get_subscriber_count(self, event_type: EventType) -> int:
        """Get number of subscribers for an event type"""
        with self._lock:
            return len(self._subscribers.get(event_type, []))
    
    def get_all_event_types(self) -> List[EventType]:
        """Get all event types that have subscribers"""
        with self._lock:
            return list(self._subscribers.keys())


# Global event system instance
event_system = EventSystem()


# Convenience functions for common events
def publish_machine_state_changed(machine_name: str, state: str, source: str = "mqtt") -> None:
    """Publish machine state change event"""
    event_system.publish(
        EventType.MACHINE_STATE_CHANGED,
        source,
        {
            "machine_name": machine_name,
            "state": state,
            "previous_state": None  # Could be enhanced to track previous state
        }
    )


def publish_camera_status_changed(camera_name: str, status: str, details: str = "", source: str = "camera_monitor") -> None:
    """Publish camera status change event"""
    event_system.publish(
        EventType.CAMERA_STATUS_CHANGED,
        source,
        {
            "camera_name": camera_name,
            "status": status,
            "details": details
        }
    )


def publish_recording_started(camera_name: str, filename: str, source: str = "recorder") -> None:
    """Publish recording started event"""
    event_system.publish(
        EventType.RECORDING_STARTED,
        source,
        {
            "camera_name": camera_name,
            "filename": filename
        }
    )


def publish_recording_stopped(camera_name: str, filename: str, duration_seconds: float, source: str = "recorder") -> None:
    """Publish recording stopped event"""
    event_system.publish(
        EventType.RECORDING_STOPPED,
        source,
        {
            "camera_name": camera_name,
            "filename": filename,
            "duration_seconds": duration_seconds
        }
    )


def publish_recording_error(camera_name: str, error_message: str, source: str = "recorder") -> None:
    """Publish recording error event"""
    event_system.publish(
        EventType.RECORDING_ERROR,
        source,
        {
            "camera_name": camera_name,
            "error_message": error_message
        }
    )
