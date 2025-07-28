"""
Storage Manager for the USDA Vision Camera System.

This module handles file organization, cleanup, and management for recorded videos.
"""

import os
import logging
import shutil
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json

from ..core.config import Config, StorageConfig
from ..core.state_manager import StateManager
from ..core.events import EventSystem, EventType, Event


class StorageManager:
    """Manages storage and file organization for recorded videos"""

    def __init__(self, config: Config, state_manager: StateManager, event_system: Optional[EventSystem] = None):
        self.config = config
        self.storage_config = config.storage
        self.state_manager = state_manager
        self.event_system = event_system
        self.logger = logging.getLogger(__name__)

        # Ensure base storage directory exists
        self._ensure_storage_structure()

        # File tracking
        self.file_index_path = os.path.join(self.storage_config.base_path, "file_index.json")
        self.file_index = self._load_file_index()

        # Subscribe to recording events if event system is available
        if self.event_system:
            self._setup_event_subscriptions()

    def _ensure_storage_structure(self) -> None:
        """Ensure storage directory structure exists"""
        try:
            # Create base storage directory
            Path(self.storage_config.base_path).mkdir(parents=True, exist_ok=True)

            # Create camera-specific directories
            for camera_config in self.config.cameras:
                Path(camera_config.storage_path).mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Ensured storage directory: {camera_config.storage_path}")

            self.logger.info("Storage directory structure verified")

        except Exception as e:
            self.logger.error(f"Error creating storage structure: {e}")
            raise

    def _setup_event_subscriptions(self) -> None:
        """Setup event subscriptions for recording tracking"""
        if not self.event_system:
            return

        def on_recording_started(event: Event):
            """Handle recording started event"""
            try:
                camera_name = event.data.get("camera_name")
                filename = event.data.get("filename")
                if camera_name and filename:
                    self.register_recording_file(camera_name=camera_name, filename=filename, start_time=event.timestamp, machine_trigger=event.data.get("machine_trigger"))
            except Exception as e:
                self.logger.error(f"Error handling recording started event: {e}")

        def on_recording_stopped(event: Event):
            """Handle recording stopped event"""
            try:
                filename = event.data.get("filename")
                if filename:
                    file_id = os.path.basename(filename)
                    self.finalize_recording_file(file_id=file_id, end_time=event.timestamp, duration_seconds=event.data.get("duration_seconds"))
            except Exception as e:
                self.logger.error(f"Error handling recording stopped event: {e}")

        # Subscribe to recording events
        self.event_system.subscribe(EventType.RECORDING_STARTED, on_recording_started)
        self.event_system.subscribe(EventType.RECORDING_STOPPED, on_recording_stopped)

    def _load_file_index(self) -> Dict[str, Any]:
        """Load file index from disk"""
        try:
            if os.path.exists(self.file_index_path):
                with open(self.file_index_path, "r") as f:
                    return json.load(f)
            else:
                return {"files": {}, "last_updated": None}
        except Exception as e:
            self.logger.error(f"Error loading file index: {e}")
            return {"files": {}, "last_updated": None}

    def _save_file_index(self) -> None:
        """Save file index to disk"""
        try:
            self.file_index["last_updated"] = datetime.now().isoformat()
            with open(self.file_index_path, "w") as f:
                json.dump(self.file_index, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving file index: {e}")

    def register_recording_file(self, camera_name: str, filename: str, start_time: datetime, machine_trigger: Optional[str] = None) -> str:
        """Register a new recording file"""
        try:
            file_id = os.path.basename(filename)

            file_info = {"camera_name": camera_name, "filename": filename, "file_id": file_id, "start_time": start_time.isoformat(), "end_time": None, "file_size_bytes": None, "duration_seconds": None, "machine_trigger": machine_trigger, "status": "recording", "created_at": datetime.now().isoformat()}

            self.file_index["files"][file_id] = file_info
            self._save_file_index()

            self.logger.info(f"Registered recording file: {file_id}")
            return file_id

        except Exception as e:
            self.logger.error(f"Error registering recording file: {e}")
            return ""

    def finalize_recording_file(self, file_id: str, end_time: datetime, duration_seconds: Optional[float] = None) -> bool:
        """Finalize a recording file when recording stops"""
        try:
            if file_id not in self.file_index["files"]:
                self.logger.warning(f"Recording file not found for finalization: {file_id}")
                return False

            file_info = self.file_index["files"][file_id]
            file_info["end_time"] = end_time.isoformat()
            file_info["status"] = "completed"

            if duration_seconds is not None:
                file_info["duration_seconds"] = duration_seconds

            # Get file size if file exists
            filename = file_info["filename"]
            if os.path.exists(filename):
                file_info["file_size_bytes"] = os.path.getsize(filename)

            self._save_file_index()
            self.logger.info(f"Finalized recording file: {file_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error finalizing recording file: {e}")
            return False

    def finalize_recording_file(self, file_id: str, end_time: datetime, duration_seconds: float, frame_count: Optional[int] = None) -> bool:
        """Finalize a recording file after recording stops"""
        try:
            if file_id not in self.file_index["files"]:
                self.logger.warning(f"File ID not found in index: {file_id}")
                return False

            file_info = self.file_index["files"][file_id]
            filename = file_info["filename"]

            # Update file information
            file_info["end_time"] = end_time.isoformat()
            file_info["duration_seconds"] = duration_seconds
            file_info["status"] = "completed"

            # Get file size if file exists
            if os.path.exists(filename):
                file_info["file_size_bytes"] = os.path.getsize(filename)

            if frame_count is not None:
                file_info["frame_count"] = frame_count

            self._save_file_index()

            self.logger.info(f"Finalized recording file: {file_id} (duration: {duration_seconds:.1f}s)")
            return True

        except Exception as e:
            self.logger.error(f"Error finalizing recording file: {e}")
            return False

    def get_recording_files(self, camera_name: Optional[str] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of recording files with optional filters"""
        try:
            files = []

            # First, get files from the index (if available)
            indexed_files = set()
            for file_id, file_info in self.file_index["files"].items():
                # Filter by camera name
                if camera_name and file_info["camera_name"] != camera_name:
                    continue

                # Filter by date range
                if start_date or end_date:
                    file_start = datetime.fromisoformat(file_info["start_time"])
                    if start_date and file_start < start_date:
                        continue
                    if end_date and file_start > end_date:
                        continue

                files.append(file_info.copy())
                indexed_files.add(file_info["filename"])

            # Then, scan filesystem for files not in the index
            for camera_config in self.config.cameras:
                # Skip if filtering by camera name and this isn't the one
                if camera_name and camera_config.name != camera_name:
                    continue

                storage_path = Path(camera_config.storage_path)
                if storage_path.exists():
                    for video_file in storage_path.glob("*.avi"):
                        if video_file.is_file() and str(video_file) not in indexed_files:
                            # Get file stats
                            stat = video_file.stat()
                            file_mtime = datetime.fromtimestamp(stat.st_mtime)

                            # Apply date filters
                            if start_date and file_mtime < start_date:
                                continue
                            if end_date and file_mtime > end_date:
                                continue

                            # Create file info for unindexed file
                            file_info = {"camera_name": camera_config.name, "filename": str(video_file), "file_id": video_file.name, "start_time": file_mtime.isoformat(), "end_time": None, "file_size_bytes": stat.st_size, "duration_seconds": None, "machine_trigger": None, "status": "unknown", "created_at": file_mtime.isoformat()}  # We don't know if it's completed or not
                            files.append(file_info)

            # Sort by start time (newest first)
            files.sort(key=lambda x: x["start_time"], reverse=True)

            # Apply limit
            if limit:
                files = files[:limit]

            return files

        except Exception as e:
            self.logger.error(f"Error getting recording files: {e}")
            return []

    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            stats = {"base_path": self.storage_config.base_path, "total_files": 0, "total_size_bytes": 0, "cameras": {}, "disk_usage": {}}

            # Get disk usage for base path
            if os.path.exists(self.storage_config.base_path):
                disk_usage = shutil.disk_usage(self.storage_config.base_path)
                stats["disk_usage"] = {"total_bytes": disk_usage.total, "used_bytes": disk_usage.used, "free_bytes": disk_usage.free, "used_percent": (disk_usage.used / disk_usage.total) * 100}

            # Scan actual filesystem for all video files
            # This ensures we count all files, not just those in the index
            for camera_config in self.config.cameras:
                camera_name = camera_config.name
                storage_path = Path(camera_config.storage_path)

                if camera_name not in stats["cameras"]:
                    stats["cameras"][camera_name] = {"file_count": 0, "total_size_bytes": 0, "total_duration_seconds": 0}

                # Scan for video files in camera directory
                if storage_path.exists():
                    for video_file in storage_path.glob("*.avi"):
                        if video_file.is_file():
                            stats["total_files"] += 1
                            stats["cameras"][camera_name]["file_count"] += 1

                            # Get file size
                            try:
                                file_size = video_file.stat().st_size
                                stats["total_size_bytes"] += file_size
                                stats["cameras"][camera_name]["total_size_bytes"] += file_size
                            except Exception as e:
                                self.logger.warning(f"Could not get size for {video_file}: {e}")

            # Add duration information from index if available
            for file_info in self.file_index["files"].values():
                camera_name = file_info["camera_name"]
                if camera_name in stats["cameras"] and file_info.get("duration_seconds"):
                    duration = file_info["duration_seconds"]
                    stats["cameras"][camera_name]["total_duration_seconds"] += duration

            return stats

        except Exception as e:
            self.logger.error(f"Error getting storage statistics: {e}")
            return {}

    def cleanup_old_files(self, max_age_days: Optional[int] = None) -> Dict[str, Any]:
        """Clean up old recording files"""
        if max_age_days is None:
            max_age_days = self.storage_config.cleanup_older_than_days

        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        cleanup_stats = {"files_removed": 0, "bytes_freed": 0, "errors": []}

        try:
            files_to_remove = []

            # Find files older than cutoff date
            for file_id, file_info in self.file_index["files"].items():
                try:
                    file_start = datetime.fromisoformat(file_info["start_time"])
                    if file_start < cutoff_date and file_info["status"] == "completed":
                        files_to_remove.append((file_id, file_info))
                except Exception as e:
                    cleanup_stats["errors"].append(f"Error parsing date for {file_id}: {e}")

            # Remove old files
            for file_id, file_info in files_to_remove:
                try:
                    filename = file_info["filename"]

                    # Remove physical file
                    if os.path.exists(filename):
                        file_size = os.path.getsize(filename)
                        os.remove(filename)
                        cleanup_stats["bytes_freed"] += file_size
                        self.logger.info(f"Removed old file: {filename}")

                    # Remove from index
                    del self.file_index["files"][file_id]
                    cleanup_stats["files_removed"] += 1

                except Exception as e:
                    error_msg = f"Error removing file {file_id}: {e}"
                    cleanup_stats["errors"].append(error_msg)
                    self.logger.error(error_msg)

            # Save updated index
            if cleanup_stats["files_removed"] > 0:
                self._save_file_index()

            self.logger.info(f"Cleanup completed: {cleanup_stats['files_removed']} files removed, " f"{cleanup_stats['bytes_freed']} bytes freed")

            return cleanup_stats

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            cleanup_stats["errors"].append(str(e))
            return cleanup_stats

    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific file"""
        return self.file_index["files"].get(file_id)

    def delete_file(self, file_id: str) -> bool:
        """Delete a specific recording file"""
        try:
            if file_id not in self.file_index["files"]:
                self.logger.warning(f"File ID not found: {file_id}")
                return False

            file_info = self.file_index["files"][file_id]
            filename = file_info["filename"]

            # Remove physical file
            if os.path.exists(filename):
                os.remove(filename)
                self.logger.info(f"Deleted file: {filename}")

            # Remove from index
            del self.file_index["files"][file_id]
            self._save_file_index()

            return True

        except Exception as e:
            self.logger.error(f"Error deleting file {file_id}: {e}")
            return False

    def verify_storage_integrity(self) -> Dict[str, Any]:
        """Verify storage integrity and fix issues"""
        integrity_report = {"total_files_in_index": len(self.file_index["files"]), "missing_files": [], "orphaned_files": [], "corrupted_entries": [], "fixed_issues": 0}

        try:
            # Check for missing files (in index but not on disk)
            for file_id, file_info in list(self.file_index["files"].items()):
                filename = file_info.get("filename")
                if filename and not os.path.exists(filename):
                    integrity_report["missing_files"].append(file_id)
                    # Remove from index
                    del self.file_index["files"][file_id]
                    integrity_report["fixed_issues"] += 1

            # Check for orphaned files (on disk but not in index)
            for camera_config in self.config.cameras:
                storage_path = Path(camera_config.storage_path)
                if storage_path.exists():
                    for video_file in storage_path.glob("*.avi"):
                        file_id = video_file.name
                        if file_id not in self.file_index["files"]:
                            integrity_report["orphaned_files"].append(str(video_file))

            # Save updated index if fixes were made
            if integrity_report["fixed_issues"] > 0:
                self._save_file_index()

            self.logger.info(f"Storage integrity check completed: {integrity_report['fixed_issues']} issues fixed")

            return integrity_report

        except Exception as e:
            self.logger.error(f"Error during integrity check: {e}")
            integrity_report["error"] = str(e)
            return integrity_report
