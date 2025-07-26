"""
State management for the USDA Vision Camera System.

This module manages the current state of machines, cameras, and recordings
in a thread-safe manner.
"""

import threading
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MachineState(Enum):
    """Machine states"""
    UNKNOWN = "unknown"
    ON = "on"
    OFF = "off"
    ERROR = "error"


class CameraStatus(Enum):
    """Camera status"""
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class RecordingState(Enum):
    """Recording states"""
    IDLE = "idle"
    RECORDING = "recording"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class MachineInfo:
    """Machine state information"""
    name: str
    state: MachineState = MachineState.UNKNOWN
    last_updated: datetime = field(default_factory=datetime.now)
    last_message: Optional[str] = None
    mqtt_topic: Optional[str] = None


@dataclass
class CameraInfo:
    """Camera state information"""
    name: str
    status: CameraStatus = CameraStatus.UNKNOWN
    last_checked: datetime = field(default_factory=datetime.now)
    last_error: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    is_recording: bool = False
    current_recording_file: Optional[str] = None
    recording_start_time: Optional[datetime] = None


@dataclass
class RecordingInfo:
    """Recording session information"""
    camera_name: str
    filename: str
    start_time: datetime
    state: RecordingState = RecordingState.RECORDING
    end_time: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    frame_count: Optional[int] = None
    error_message: Optional[str] = None


class StateManager:
    """Thread-safe state manager for the entire system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        
        # State dictionaries
        self._machines: Dict[str, MachineInfo] = {}
        self._cameras: Dict[str, CameraInfo] = {}
        self._recordings: Dict[str, RecordingInfo] = {}  # Key: recording_id (filename)
        
        # System state
        self._mqtt_connected = False
        self._system_started = False
        self._last_mqtt_message_time: Optional[datetime] = None
    
    # Machine state management
    def update_machine_state(self, name: str, state: str, message: Optional[str] = None, topic: Optional[str] = None) -> bool:
        """Update machine state"""
        try:
            machine_state = MachineState(state.lower())
        except ValueError:
            self.logger.warning(f"Invalid machine state: {state}")
            machine_state = MachineState.UNKNOWN
        
        with self._lock:
            if name not in self._machines:
                self._machines[name] = MachineInfo(name=name, mqtt_topic=topic)
            
            machine = self._machines[name]
            old_state = machine.state
            machine.state = machine_state
            machine.last_updated = datetime.now()
            machine.last_message = message
            if topic:
                machine.mqtt_topic = topic
            
            self.logger.info(f"Machine {name} state: {old_state.value} -> {machine_state.value}")
            return old_state != machine_state
    
    def get_machine_state(self, name: str) -> Optional[MachineInfo]:
        """Get machine state"""
        with self._lock:
            return self._machines.get(name)
    
    def get_all_machines(self) -> Dict[str, MachineInfo]:
        """Get all machine states"""
        with self._lock:
            return self._machines.copy()
    
    # Camera state management
    def update_camera_status(self, name: str, status: str, error: Optional[str] = None, device_info: Optional[Dict] = None) -> bool:
        """Update camera status"""
        try:
            camera_status = CameraStatus(status.lower())
        except ValueError:
            self.logger.warning(f"Invalid camera status: {status}")
            camera_status = CameraStatus.UNKNOWN
        
        with self._lock:
            if name not in self._cameras:
                self._cameras[name] = CameraInfo(name=name)
            
            camera = self._cameras[name]
            old_status = camera.status
            camera.status = camera_status
            camera.last_checked = datetime.now()
            camera.last_error = error
            if device_info:
                camera.device_info = device_info
            
            if old_status != camera_status:
                self.logger.info(f"Camera {name} status: {old_status.value} -> {camera_status.value}")
                return True
            return False
    
    def set_camera_recording(self, name: str, recording: bool, filename: Optional[str] = None) -> None:
        """Set camera recording state"""
        with self._lock:
            if name not in self._cameras:
                self._cameras[name] = CameraInfo(name=name)
            
            camera = self._cameras[name]
            camera.is_recording = recording
            camera.current_recording_file = filename
            
            if recording and filename:
                camera.recording_start_time = datetime.now()
                self.logger.info(f"Camera {name} started recording: {filename}")
            elif not recording:
                camera.recording_start_time = None
                self.logger.info(f"Camera {name} stopped recording")
    
    def get_camera_status(self, name: str) -> Optional[CameraInfo]:
        """Get camera status"""
        with self._lock:
            return self._cameras.get(name)
    
    def get_all_cameras(self) -> Dict[str, CameraInfo]:
        """Get all camera statuses"""
        with self._lock:
            return self._cameras.copy()
    
    # Recording management
    def start_recording(self, camera_name: str, filename: str) -> str:
        """Start a new recording session"""
        recording_id = filename  # Use filename as recording ID
        
        with self._lock:
            recording = RecordingInfo(
                camera_name=camera_name,
                filename=filename,
                start_time=datetime.now()
            )
            self._recordings[recording_id] = recording
            
            # Update camera state
            self.set_camera_recording(camera_name, True, filename)
            
            self.logger.info(f"Started recording session: {recording_id}")
            return recording_id
    
    def stop_recording(self, recording_id: str, file_size: Optional[int] = None, frame_count: Optional[int] = None) -> bool:
        """Stop a recording session"""
        with self._lock:
            if recording_id not in self._recordings:
                self.logger.warning(f"Recording session not found: {recording_id}")
                return False
            
            recording = self._recordings[recording_id]
            recording.state = RecordingState.IDLE
            recording.end_time = datetime.now()
            recording.file_size_bytes = file_size
            recording.frame_count = frame_count
            
            # Update camera state
            self.set_camera_recording(recording.camera_name, False)
            
            duration = (recording.end_time - recording.start_time).total_seconds()
            self.logger.info(f"Stopped recording session: {recording_id} (duration: {duration:.1f}s)")
            return True
    
    def set_recording_error(self, recording_id: str, error_message: str) -> bool:
        """Set recording error state"""
        with self._lock:
            if recording_id not in self._recordings:
                return False
            
            recording = self._recordings[recording_id]
            recording.state = RecordingState.ERROR
            recording.error_message = error_message
            recording.end_time = datetime.now()
            
            # Update camera state
            self.set_camera_recording(recording.camera_name, False)
            
            self.logger.error(f"Recording error for {recording_id}: {error_message}")
            return True
    
    def get_recording(self, recording_id: str) -> Optional[RecordingInfo]:
        """Get recording information"""
        with self._lock:
            return self._recordings.get(recording_id)
    
    def get_all_recordings(self) -> Dict[str, RecordingInfo]:
        """Get all recording sessions"""
        with self._lock:
            return self._recordings.copy()
    
    def get_active_recordings(self) -> Dict[str, RecordingInfo]:
        """Get currently active recordings"""
        with self._lock:
            return {
                rid: recording for rid, recording in self._recordings.items()
                if recording.state == RecordingState.RECORDING
            }
    
    # System state management
    def set_mqtt_connected(self, connected: bool) -> None:
        """Set MQTT connection state"""
        with self._lock:
            old_state = self._mqtt_connected
            self._mqtt_connected = connected
            if connected:
                self._last_mqtt_message_time = datetime.now()
            
            if old_state != connected:
                self.logger.info(f"MQTT connection: {'connected' if connected else 'disconnected'}")
    
    def is_mqtt_connected(self) -> bool:
        """Check if MQTT is connected"""
        with self._lock:
            return self._mqtt_connected
    
    def update_mqtt_activity(self) -> None:
        """Update last MQTT message time"""
        with self._lock:
            self._last_mqtt_message_time = datetime.now()
    
    def set_system_started(self, started: bool) -> None:
        """Set system started state"""
        with self._lock:
            self._system_started = started
            self.logger.info(f"System {'started' if started else 'stopped'}")
    
    def is_system_started(self) -> bool:
        """Check if system is started"""
        with self._lock:
            return self._system_started
    
    # Utility methods
    def get_system_summary(self) -> Dict[str, Any]:
        """Get a summary of the entire system state"""
        with self._lock:
            return {
                "system_started": self._system_started,
                "mqtt_connected": self._mqtt_connected,
                "last_mqtt_message": self._last_mqtt_message_time.isoformat() if self._last_mqtt_message_time else None,
                "machines": {name: {
                    "state": machine.state.value,
                    "last_updated": machine.last_updated.isoformat()
                } for name, machine in self._machines.items()},
                "cameras": {name: {
                    "status": camera.status.value,
                    "is_recording": camera.is_recording,
                    "last_checked": camera.last_checked.isoformat()
                } for name, camera in self._cameras.items()},
                "active_recordings": len(self.get_active_recordings()),
                "total_recordings": len(self._recordings)
            }
    
    def cleanup_old_recordings(self, max_age_hours: int = 24) -> int:
        """Clean up old recording entries from memory"""
        cutoff_time = datetime.now() - datetime.timedelta(hours=max_age_hours)
        removed_count = 0
        
        with self._lock:
            to_remove = []
            for recording_id, recording in self._recordings.items():
                if (recording.state != RecordingState.RECORDING and 
                    recording.end_time and recording.end_time < cutoff_time):
                    to_remove.append(recording_id)
            
            for recording_id in to_remove:
                del self._recordings[recording_id]
                removed_count += 1
        
        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} old recording entries")
        
        return removed_count
