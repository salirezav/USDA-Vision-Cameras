"""
FastAPI Server for the USDA Vision Camera System.

This module provides REST API endpoints and WebSocket support for dashboard integration.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn

from ..core.config import Config
from ..core.state_manager import StateManager
from ..core.events import EventSystem, EventType, Event
from ..storage.manager import StorageManager
from .models import *


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logging.getLogger(f"{__name__}.WebSocketManager")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            self.logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)


class APIServer:
    """FastAPI server for the USDA Vision Camera System"""

    def __init__(self, config: Config, state_manager: StateManager, event_system: EventSystem, camera_manager, mqtt_client, storage_manager: StorageManager, auto_recording_manager=None):
        self.config = config
        self.state_manager = state_manager
        self.event_system = event_system
        self.camera_manager = camera_manager
        self.mqtt_client = mqtt_client
        self.storage_manager = storage_manager
        self.auto_recording_manager = auto_recording_manager
        self.logger = logging.getLogger(__name__)

        # FastAPI app
        self.app = FastAPI(title="USDA Vision Camera System API", description="API for monitoring and controlling the USDA vision camera system", version="1.0.0")

        # WebSocket manager
        self.websocket_manager = WebSocketManager()

        # Server state
        self.server_start_time = datetime.now()
        self.running = False
        self._server_thread: Optional[threading.Thread] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        # Setup CORS
        self.app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])  # Configure appropriately for production

        # Setup routes
        self._setup_routes()

        # Subscribe to events for WebSocket broadcasting
        self._setup_event_subscriptions()

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/", response_model=SuccessResponse)
        async def root():
            return SuccessResponse(message="USDA Vision Camera System API")

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        @self.app.get("/system/status", response_model=SystemStatusResponse)
        async def get_system_status():
            """Get overall system status"""
            try:
                summary = self.state_manager.get_system_summary()
                uptime = (datetime.now() - self.server_start_time).total_seconds()

                return SystemStatusResponse(system_started=summary["system_started"], mqtt_connected=summary["mqtt_connected"], last_mqtt_message=summary["last_mqtt_message"], machines=summary["machines"], cameras=summary["cameras"], active_recordings=summary["active_recordings"], total_recordings=summary["total_recordings"], uptime_seconds=uptime)
            except Exception as e:
                self.logger.error(f"Error getting system status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/machines", response_model=Dict[str, MachineStatusResponse])
        async def get_machines():
            """Get all machine statuses"""
            try:
                machines = self.state_manager.get_all_machines()
                return {name: MachineStatusResponse(name=machine.name, state=machine.state.value, last_updated=machine.last_updated.isoformat(), last_message=machine.last_message, mqtt_topic=machine.mqtt_topic) for name, machine in machines.items()}
            except Exception as e:
                self.logger.error(f"Error getting machines: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/mqtt/status", response_model=MQTTStatusResponse)
        async def get_mqtt_status():
            """Get MQTT client status and statistics"""
            try:
                status = self.mqtt_client.get_status()
                return MQTTStatusResponse(connected=status["connected"], broker_host=status["broker_host"], broker_port=status["broker_port"], subscribed_topics=status["subscribed_topics"], last_message_time=status["last_message_time"], message_count=status["message_count"], error_count=status["error_count"], uptime_seconds=status["uptime_seconds"])
            except Exception as e:
                self.logger.error(f"Error getting MQTT status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/mqtt/events", response_model=MQTTEventsHistoryResponse)
        async def get_mqtt_events(limit: int = Query(default=5, ge=1, le=50, description="Number of recent events to retrieve")):
            """Get recent MQTT events history"""
            try:
                events = self.state_manager.get_recent_mqtt_events(limit)
                total_events = self.state_manager.get_mqtt_event_count()

                # Convert events to response format
                event_responses = [MQTTEventResponse(machine_name=event.machine_name, topic=event.topic, payload=event.payload, normalized_state=event.normalized_state, timestamp=event.timestamp.isoformat(), message_number=event.message_number) for event in events]

                last_updated = events[0].timestamp.isoformat() if events else None

                return MQTTEventsHistoryResponse(events=event_responses, total_events=total_events, last_updated=last_updated)
            except Exception as e:
                self.logger.error(f"Error getting MQTT events: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/cameras", response_model=Dict[str, CameraStatusResponse])
        async def get_cameras():
            """Get all camera statuses"""
            try:
                cameras = self.state_manager.get_all_cameras()
                return {
                    name: CameraStatusResponse(
                        name=camera.name,
                        status=camera.status.value,
                        is_recording=camera.is_recording,
                        last_checked=camera.last_checked.isoformat(),
                        last_error=camera.last_error,
                        device_info=camera.device_info,
                        current_recording_file=camera.current_recording_file,
                        recording_start_time=camera.recording_start_time.isoformat() if camera.recording_start_time else None,
                        auto_recording_enabled=camera.auto_recording_enabled,
                        auto_recording_active=camera.auto_recording_active,
                        auto_recording_failure_count=camera.auto_recording_failure_count,
                        auto_recording_last_attempt=camera.auto_recording_last_attempt.isoformat() if camera.auto_recording_last_attempt else None,
                        auto_recording_last_error=camera.auto_recording_last_error,
                    )
                    for name, camera in cameras.items()
                }
            except Exception as e:
                self.logger.error(f"Error getting cameras: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/cameras/{camera_name}/status", response_model=CameraStatusResponse)
        async def get_camera_status(camera_name: str):
            """Get specific camera status"""
            try:
                camera = self.state_manager.get_camera_status(camera_name)
                if not camera:
                    raise HTTPException(status_code=404, detail=f"Camera not found: {camera_name}")

                return CameraStatusResponse(name=camera.name, status=camera.status.value, is_recording=camera.is_recording, last_checked=camera.last_checked.isoformat(), last_error=camera.last_error, device_info=camera.device_info, current_recording_file=camera.current_recording_file, recording_start_time=camera.recording_start_time.isoformat() if camera.recording_start_time else None)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting camera status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/start-recording", response_model=StartRecordingResponse)
        async def start_recording(camera_name: str, request: StartRecordingRequest):
            """Manually start recording for a camera"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.manual_start_recording(camera_name=camera_name, filename=request.filename, exposure_ms=request.exposure_ms, gain=request.gain, fps=request.fps)

                if success:
                    # Get the actual filename that was used (with datetime prefix)
                    actual_filename = request.filename
                    if request.filename:
                        from ..core.timezone_utils import format_filename_timestamp

                        timestamp = format_filename_timestamp()
                        actual_filename = f"{timestamp}_{request.filename}"

                    return StartRecordingResponse(success=True, message=f"Recording started for {camera_name}", filename=actual_filename)
                else:
                    return StartRecordingResponse(success=False, message=f"Failed to start recording for {camera_name}")
            except Exception as e:
                self.logger.error(f"Error starting recording: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/stop-recording", response_model=StopRecordingResponse)
        async def stop_recording(camera_name: str):
            """Manually stop recording for a camera"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.manual_stop_recording(camera_name)

                if success:
                    return StopRecordingResponse(success=True, message=f"Recording stopped for {camera_name}")
                else:
                    return StopRecordingResponse(success=False, message=f"Failed to stop recording for {camera_name}")
            except Exception as e:
                self.logger.error(f"Error stopping recording: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/test-connection", response_model=CameraTestResponse)
        async def test_camera_connection(camera_name: str):
            """Test camera connection"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.test_camera_connection(camera_name)

                if success:
                    return CameraTestResponse(success=True, message=f"Camera {camera_name} connection test passed", camera_name=camera_name)
                else:
                    return CameraTestResponse(success=False, message=f"Camera {camera_name} connection test failed", camera_name=camera_name)
            except Exception as e:
                self.logger.error(f"Error testing camera connection: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/cameras/{camera_name}/stream")
        async def camera_stream(camera_name: str):
            """Get live MJPEG stream from camera"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                # Get camera streamer
                streamer = self.camera_manager.get_camera_streamer(camera_name)
                if not streamer:
                    raise HTTPException(status_code=404, detail=f"Camera {camera_name} not found")

                # Start streaming if not already active
                if not streamer.is_streaming():
                    success = streamer.start_streaming()
                    if not success:
                        raise HTTPException(status_code=500, detail=f"Failed to start streaming for camera {camera_name}")

                # Return MJPEG stream
                return StreamingResponse(streamer.get_frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error starting camera stream: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/start-stream")
        async def start_camera_stream(camera_name: str):
            """Start streaming for a camera"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.start_camera_streaming(camera_name)
                if success:
                    return {"success": True, "message": f"Started streaming for camera {camera_name}"}
                else:
                    return {"success": False, "message": f"Failed to start streaming for camera {camera_name}"}

            except Exception as e:
                self.logger.error(f"Error starting camera stream: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/stop-stream")
        async def stop_camera_stream(camera_name: str):
            """Stop streaming for a camera"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.stop_camera_streaming(camera_name)
                if success:
                    return {"success": True, "message": f"Stopped streaming for camera {camera_name}"}
                else:
                    return {"success": False, "message": f"Failed to stop streaming for camera {camera_name}"}

            except Exception as e:
                self.logger.error(f"Error stopping camera stream: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/cameras/{camera_name}/config", response_model=CameraConfigResponse)
        async def get_camera_config(camera_name: str):
            """Get camera configuration"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                config = self.camera_manager.get_camera_config(camera_name)
                if not config:
                    raise HTTPException(status_code=404, detail=f"Camera {camera_name} not found")

                return CameraConfigResponse(
                    name=config.name,
                    machine_topic=config.machine_topic,
                    storage_path=config.storage_path,
                    enabled=config.enabled,
                    # Auto-recording settings
                    auto_start_recording_enabled=config.auto_start_recording_enabled,
                    auto_recording_max_retries=config.auto_recording_max_retries,
                    auto_recording_retry_delay_seconds=config.auto_recording_retry_delay_seconds,
                    # Basic settings
                    exposure_ms=config.exposure_ms,
                    gain=config.gain,
                    target_fps=config.target_fps,
                    # Image Quality Settings
                    sharpness=config.sharpness,
                    contrast=config.contrast,
                    saturation=config.saturation,
                    gamma=config.gamma,
                    # Noise Reduction
                    noise_filter_enabled=config.noise_filter_enabled,
                    denoise_3d_enabled=config.denoise_3d_enabled,
                    # Color Settings
                    auto_white_balance=config.auto_white_balance,
                    color_temperature_preset=config.color_temperature_preset,
                    # Advanced Settings
                    anti_flicker_enabled=config.anti_flicker_enabled,
                    light_frequency=config.light_frequency,
                    bit_depth=config.bit_depth,
                    # HDR Settings
                    hdr_enabled=config.hdr_enabled,
                    hdr_gain_mode=config.hdr_gain_mode,
                )

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting camera config: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put("/cameras/{camera_name}/config")
        async def update_camera_config(camera_name: str, request: CameraConfigRequest):
            """Update camera configuration"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                # Convert request to dict, excluding None values
                config_updates = {k: v for k, v in request.dict().items() if v is not None}

                if not config_updates:
                    raise HTTPException(status_code=400, detail="No configuration updates provided")

                success = self.camera_manager.update_camera_config(camera_name, **config_updates)
                if success:
                    return {"success": True, "message": f"Camera {camera_name} configuration updated", "updated_settings": list(config_updates.keys())}
                else:
                    raise HTTPException(status_code=404, detail=f"Camera {camera_name} not found or update failed")

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error updating camera config: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/apply-config")
        async def apply_camera_config(camera_name: str):
            """Apply current configuration to active camera (requires camera restart)"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.apply_camera_config(camera_name)
                if success:
                    return {"success": True, "message": f"Configuration applied to camera {camera_name}"}
                else:
                    return {"success": False, "message": f"Failed to apply configuration to camera {camera_name}"}

            except Exception as e:
                self.logger.error(f"Error applying camera config: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/reconnect", response_model=CameraRecoveryResponse)
        async def reconnect_camera(camera_name: str):
            """Reconnect to a camera"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.reconnect_camera(camera_name)

                if success:
                    return CameraRecoveryResponse(success=True, message=f"Camera {camera_name} reconnected successfully", camera_name=camera_name, operation="reconnect")
                else:
                    return CameraRecoveryResponse(success=False, message=f"Failed to reconnect camera {camera_name}", camera_name=camera_name, operation="reconnect")
            except Exception as e:
                self.logger.error(f"Error reconnecting camera: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/restart-grab", response_model=CameraRecoveryResponse)
        async def restart_camera_grab(camera_name: str):
            """Restart camera grab process"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.restart_camera_grab(camera_name)

                if success:
                    return CameraRecoveryResponse(success=True, message=f"Camera {camera_name} grab process restarted successfully", camera_name=camera_name, operation="restart-grab")
                else:
                    return CameraRecoveryResponse(success=False, message=f"Failed to restart grab process for camera {camera_name}", camera_name=camera_name, operation="restart-grab")
            except Exception as e:
                self.logger.error(f"Error restarting camera grab: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/reset-timestamp", response_model=CameraRecoveryResponse)
        async def reset_camera_timestamp(camera_name: str):
            """Reset camera timestamp"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.reset_camera_timestamp(camera_name)

                if success:
                    return CameraRecoveryResponse(success=True, message=f"Camera {camera_name} timestamp reset successfully", camera_name=camera_name, operation="reset-timestamp")
                else:
                    return CameraRecoveryResponse(success=False, message=f"Failed to reset timestamp for camera {camera_name}", camera_name=camera_name, operation="reset-timestamp")
            except Exception as e:
                self.logger.error(f"Error resetting camera timestamp: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/full-reset", response_model=CameraRecoveryResponse)
        async def full_reset_camera(camera_name: str):
            """Perform full camera reset (uninitialize and reinitialize)"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.full_reset_camera(camera_name)

                if success:
                    return CameraRecoveryResponse(success=True, message=f"Camera {camera_name} full reset completed successfully", camera_name=camera_name, operation="full-reset")
                else:
                    return CameraRecoveryResponse(success=False, message=f"Failed to perform full reset for camera {camera_name}", camera_name=camera_name, operation="full-reset")
            except Exception as e:
                self.logger.error(f"Error performing full camera reset: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/reinitialize", response_model=CameraRecoveryResponse)
        async def reinitialize_camera(camera_name: str):
            """Reinitialize a failed camera"""
            try:
                if not self.camera_manager:
                    raise HTTPException(status_code=503, detail="Camera manager not available")

                success = self.camera_manager.reinitialize_failed_camera(camera_name)

                if success:
                    return CameraRecoveryResponse(success=True, message=f"Camera {camera_name} reinitialized successfully", camera_name=camera_name, operation="reinitialize")
                else:
                    return CameraRecoveryResponse(success=False, message=f"Failed to reinitialize camera {camera_name}", camera_name=camera_name, operation="reinitialize")
            except Exception as e:
                self.logger.error(f"Error reinitializing camera: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/auto-recording/enable", response_model=AutoRecordingConfigResponse)
        async def enable_auto_recording(camera_name: str):
            """Enable auto-recording for a camera"""
            try:
                if not self.auto_recording_manager:
                    raise HTTPException(status_code=503, detail="Auto-recording manager not available")

                # Update camera configuration
                camera_config = self.config.get_camera_by_name(camera_name)
                if not camera_config:
                    raise HTTPException(status_code=404, detail=f"Camera {camera_name} not found")

                camera_config.auto_start_recording_enabled = True
                self.config.save_config()

                # Update camera status in state manager
                camera_info = self.state_manager.get_camera_info(camera_name)
                if camera_info:
                    camera_info.auto_recording_enabled = True

                return AutoRecordingConfigResponse(success=True, message=f"Auto-recording enabled for camera {camera_name}", camera_name=camera_name, enabled=True)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error enabling auto-recording for camera {camera_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/cameras/{camera_name}/auto-recording/disable", response_model=AutoRecordingConfigResponse)
        async def disable_auto_recording(camera_name: str):
            """Disable auto-recording for a camera"""
            try:
                if not self.auto_recording_manager:
                    raise HTTPException(status_code=503, detail="Auto-recording manager not available")

                # Update camera configuration
                camera_config = self.config.get_camera_by_name(camera_name)
                if not camera_config:
                    raise HTTPException(status_code=404, detail=f"Camera {camera_name} not found")

                camera_config.auto_start_recording_enabled = False
                self.config.save_config()

                # Update camera status in state manager
                camera_info = self.state_manager.get_camera_info(camera_name)
                if camera_info:
                    camera_info.auto_recording_enabled = False
                    camera_info.auto_recording_active = False

                return AutoRecordingConfigResponse(success=True, message=f"Auto-recording disabled for camera {camera_name}", camera_name=camera_name, enabled=False)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error disabling auto-recording for camera {camera_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/auto-recording/status", response_model=AutoRecordingStatusResponse)
        async def get_auto_recording_status():
            """Get auto-recording manager status"""
            try:
                if not self.auto_recording_manager:
                    raise HTTPException(status_code=503, detail="Auto-recording manager not available")

                status = self.auto_recording_manager.get_status()
                return AutoRecordingStatusResponse(**status)
            except Exception as e:
                self.logger.error(f"Error getting auto-recording status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/recordings", response_model=Dict[str, RecordingInfoResponse])
        async def get_recordings():
            """Get all recording sessions"""
            try:
                recordings = self.state_manager.get_all_recordings()
                return {
                    rid: RecordingInfoResponse(
                        camera_name=recording.camera_name,
                        filename=recording.filename,
                        start_time=recording.start_time.isoformat(),
                        state=recording.state.value,
                        end_time=recording.end_time.isoformat() if recording.end_time else None,
                        file_size_bytes=recording.file_size_bytes,
                        frame_count=recording.frame_count,
                        duration_seconds=(recording.end_time - recording.start_time).total_seconds() if recording.end_time else None,
                        error_message=recording.error_message,
                    )
                    for rid, recording in recordings.items()
                }
            except Exception as e:
                self.logger.error(f"Error getting recordings: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/storage/stats", response_model=StorageStatsResponse)
        async def get_storage_stats():
            """Get storage statistics"""
            try:
                stats = self.storage_manager.get_storage_statistics()
                return StorageStatsResponse(**stats)
            except Exception as e:
                self.logger.error(f"Error getting storage stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/storage/files", response_model=FileListResponse)
        async def get_files(request: FileListRequest):
            """Get list of recording files"""
            try:
                start_date = None
                end_date = None

                if request.start_date:
                    start_date = datetime.fromisoformat(request.start_date)
                if request.end_date:
                    end_date = datetime.fromisoformat(request.end_date)

                files = self.storage_manager.get_recording_files(camera_name=request.camera_name, start_date=start_date, end_date=end_date, limit=request.limit)

                return FileListResponse(files=files, total_count=len(files))
            except Exception as e:
                self.logger.error(f"Error getting files: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/storage/cleanup", response_model=CleanupResponse)
        async def cleanup_storage(request: CleanupRequest):
            """Clean up old storage files"""
            try:
                result = self.storage_manager.cleanup_old_files(request.max_age_days)
                return CleanupResponse(**result)
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await self.websocket_manager.connect(websocket)
            try:
                while True:
                    # Keep connection alive and handle incoming messages
                    data = await websocket.receive_text()
                    # Echo back for now - could implement commands later
                    await self.websocket_manager.send_personal_message({"type": "echo", "data": data}, websocket)
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)

    def _setup_event_subscriptions(self):
        """Setup event subscriptions for WebSocket broadcasting"""

        def broadcast_event(event: Event):
            """Broadcast event to all WebSocket connections"""
            try:
                message = {"type": "event", "event_type": event.event_type.value, "source": event.source, "data": event.data, "timestamp": event.timestamp.isoformat()}

                # Schedule the broadcast in the event loop thread-safely
                if self._event_loop and not self._event_loop.is_closed():
                    # Use call_soon_threadsafe to schedule the coroutine from another thread
                    asyncio.run_coroutine_threadsafe(self.websocket_manager.broadcast(message), self._event_loop)
                else:
                    self.logger.debug("Event loop not available for broadcasting")

            except Exception as e:
                self.logger.error(f"Error broadcasting event: {e}")

        # Subscribe to all event types for broadcasting
        for event_type in EventType:
            self.event_system.subscribe(event_type, broadcast_event)

    def start(self) -> bool:
        """Start the API server"""
        if self.running:
            self.logger.warning("API server is already running")
            return True

        if not self.config.system.enable_api:
            self.logger.info("API server disabled in configuration")
            return False

        try:
            self.logger.info(f"Starting API server on {self.config.system.api_host}:{self.config.system.api_port}")
            self.running = True

            # Start server in separate thread
            self._server_thread = threading.Thread(target=self._run_server, daemon=True)
            self._server_thread.start()

            return True

        except Exception as e:
            self.logger.error(f"Error starting API server: {e}")
            return False

    def stop(self) -> None:
        """Stop the API server"""
        if not self.running:
            return

        self.logger.info("Stopping API server...")
        self.running = False

        # Note: uvicorn doesn't have a clean way to stop from another thread
        # In production, you might want to use a process manager like gunicorn

        self.logger.info("API server stopped")

    def _run_server(self) -> None:
        """Run the uvicorn server"""
        try:
            # Capture the event loop for thread-safe event broadcasting
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)

            uvicorn.run(self.app, host=self.config.system.api_host, port=self.config.system.api_port, log_level="info")
        except Exception as e:
            self.logger.error(f"Error running API server: {e}")
        finally:
            self.running = False
            self._event_loop = None

    def is_running(self) -> bool:
        """Check if API server is running"""
        return self.running

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {"running": self.running, "host": self.config.system.api_host, "port": self.config.system.api_port, "start_time": self.server_start_time.isoformat(), "uptime_seconds": (datetime.now() - self.server_start_time).total_seconds(), "websocket_connections": len(self.websocket_manager.active_connections)}
