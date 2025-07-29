"""
Main Application Coordinator for the USDA Vision Camera System.

This module coordinates all system components and provides graceful startup/shutdown.
"""

import signal
import time
import logging
import sys
from typing import Optional
from datetime import datetime

from .core.config import Config
from .core.state_manager import StateManager
from .core.events import EventSystem, EventType
from .core.logging_config import setup_logging, get_error_tracker, get_performance_logger
from .core.timezone_utils import log_time_info, check_time_sync
from .mqtt.client import MQTTClient
from .camera.manager import CameraManager
from .storage.manager import StorageManager
from .recording.auto_manager import AutoRecordingManager
from .api.server import APIServer


class USDAVisionSystem:
    """Main application coordinator for the USDA Vision Camera System"""

    def __init__(self, config_file: Optional[str] = None):
        # Load configuration first (basic logging will be used initially)
        self.config = Config(config_file)

        # Setup comprehensive logging
        self.logger_setup = setup_logging(log_level=self.config.system.log_level, log_file=self.config.system.log_file)
        self.logger = logging.getLogger(__name__)

        # Setup error tracking and performance monitoring
        self.error_tracker = get_error_tracker("main_system")
        self.performance_logger = get_performance_logger("main_system")

        # Initialize core components
        self.state_manager = StateManager()
        self.event_system = EventSystem()

        # Initialize system components
        self.storage_manager = StorageManager(self.config, self.state_manager, self.event_system)
        self.mqtt_client = MQTTClient(self.config, self.state_manager, self.event_system)
        self.camera_manager = CameraManager(self.config, self.state_manager, self.event_system)
        self.auto_recording_manager = AutoRecordingManager(self.config, self.state_manager, self.event_system, self.camera_manager)
        self.api_server = APIServer(self.config, self.state_manager, self.event_system, self.camera_manager, self.mqtt_client, self.storage_manager, self.auto_recording_manager)

        # System state
        self.running = False
        self.start_time: Optional[datetime] = None

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        self.logger.info("USDA Vision Camera System initialized")

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start(self) -> bool:
        """Start the entire system"""
        if self.running:
            self.logger.warning("System is already running")
            return True

        self.logger.info("Starting USDA Vision Camera System...")
        self.performance_logger.start_timer("system_startup")
        self.start_time = datetime.now()

        # Check time synchronization
        self.logger.info("Checking time synchronization...")
        log_time_info(self.logger)
        sync_info = check_time_sync()
        if sync_info["sync_status"] == "out_of_sync":
            self.error_tracker.log_warning(f"System time may be out of sync (difference: {sync_info.get('time_diff_seconds', 'unknown')}s)", "time_sync_check")
        elif sync_info["sync_status"] == "synchronized":
            self.logger.info("✅ System time is synchronized")

        try:
            # Start storage manager (no background tasks)
            self.logger.info("Initializing storage manager...")
            try:
                # Verify storage integrity
                integrity_report = self.storage_manager.verify_storage_integrity()
                if integrity_report.get("fixed_issues", 0) > 0:
                    self.logger.info(f"Fixed {integrity_report['fixed_issues']} storage integrity issues")
                self.logger.info("Storage manager ready")
            except Exception as e:
                self.error_tracker.log_error(e, "storage_manager_init")
                self.logger.error("Failed to initialize storage manager")
                return False

            # Start MQTT client
            self.logger.info("Starting MQTT client...")
            try:
                if not self.mqtt_client.start():
                    self.error_tracker.log_error(Exception("MQTT client failed to start"), "mqtt_startup")
                    return False
                self.logger.info("MQTT client started successfully")
            except Exception as e:
                self.error_tracker.log_error(e, "mqtt_startup")
                return False

            # Start camera manager
            self.logger.info("Starting camera manager...")
            try:
                if not self.camera_manager.start():
                    self.error_tracker.log_error(Exception("Camera manager failed to start"), "camera_startup")
                    self.mqtt_client.stop()
                    return False
                self.logger.info("Camera manager started successfully")
            except Exception as e:
                self.error_tracker.log_error(e, "camera_startup")
                self.mqtt_client.stop()
                return False

            # Start auto-recording manager
            self.logger.info("Starting auto-recording manager...")
            try:
                if not self.auto_recording_manager.start():
                    self.error_tracker.log_warning("Failed to start auto-recording manager", "auto_recording_startup")
                else:
                    self.logger.info("Auto-recording manager started successfully")
            except Exception as e:
                self.error_tracker.log_error(e, "auto_recording_startup")
                self.logger.warning("Auto-recording manager failed to start (continuing without auto-recording)")

            # Start API server
            self.logger.info("Starting API server...")
            try:
                if not self.api_server.start():
                    self.error_tracker.log_warning("Failed to start API server", "api_startup")
                else:
                    self.logger.info("API server started successfully")
            except Exception as e:
                self.error_tracker.log_error(e, "api_startup")
                self.logger.warning("API server failed to start (continuing without API)")

            # Update system state
            self.running = True
            self.state_manager.set_system_started(True)

            # Publish system started event
            self.event_system.publish(EventType.SYSTEM_SHUTDOWN, "main_system", {"action": "started", "timestamp": self.start_time.isoformat()})  # We don't have SYSTEM_STARTED, using closest

            startup_time = self.performance_logger.end_timer("system_startup")
            self.logger.info(f"USDA Vision Camera System started successfully in {startup_time:.2f}s")
            return True

        except Exception as e:
            self.error_tracker.log_error(e, "system_startup")
            self.stop()
            return False

    def stop(self) -> None:
        """Stop the entire system gracefully"""
        if not self.running:
            return

        self.logger.info("Stopping USDA Vision Camera System...")
        self.running = False

        try:
            # Update system state
            self.state_manager.set_system_started(False)

            # Publish system shutdown event
            self.event_system.publish(EventType.SYSTEM_SHUTDOWN, "main_system", {"action": "stopping", "timestamp": datetime.now().isoformat()})

            # Stop API server
            self.api_server.stop()

            # Stop auto-recording manager
            self.auto_recording_manager.stop()

            # Stop camera manager (this will stop all recordings)
            self.camera_manager.stop()

            # Stop MQTT client
            self.mqtt_client.stop()

            # Final cleanup
            if self.start_time:
                uptime = (datetime.now() - self.start_time).total_seconds()
                self.logger.info(f"System uptime: {uptime:.1f} seconds")

            self.logger.info("USDA Vision Camera System stopped")

        except Exception as e:
            self.logger.error(f"Error during system shutdown: {e}")

    def run(self) -> None:
        """Run the system (blocking call)"""
        if not self.start():
            self.logger.error("Failed to start system")
            return

        try:
            self.logger.info("System running... Press Ctrl+C to stop")

            # Main loop - just keep the system alive
            while self.running:
                time.sleep(1)

                # Periodic maintenance tasks could go here
                # For example: cleanup old recordings, health checks, etc.

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop()

    def get_system_status(self) -> dict:
        """Get comprehensive system status"""
        return {
            "running": self.running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "components": {"mqtt_client": {"running": self.mqtt_client.is_running(), "connected": self.mqtt_client.is_connected()}, "camera_manager": {"running": self.camera_manager.is_running()}, "api_server": {"running": self.api_server.is_running()}},
            "state_summary": self.state_manager.get_system_summary(),
        }

    def is_running(self) -> bool:
        """Check if system is running"""
        return self.running


def main():
    """Main entry point for the application"""
    import argparse

    parser = argparse.ArgumentParser(description="USDA Vision Camera System")
    parser.add_argument("--config", type=str, help="Path to configuration file", default="config.json")
    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Override log level", default=None)

    args = parser.parse_args()

    # Create and run system
    system = USDAVisionSystem(args.config)

    # Override log level if specified
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))

    try:
        system.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
