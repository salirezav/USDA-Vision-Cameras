#!/usr/bin/env python3
"""
Video Reindexing Script for USDA Vision Camera System

This script reindexes existing video files that have "unknown" status,
updating them to "completed" status so they can be streamed.

Usage:
    python reindex_videos.py [--dry-run] [--camera CAMERA_NAME]
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from usda_vision_system.core.config import Config
from usda_vision_system.core.state_manager import StateManager
from usda_vision_system.storage.manager import StorageManager


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def reindex_videos(storage_manager: StorageManager, camera_name: str = None, dry_run: bool = False):
    """
    Reindex video files with unknown status
    
    Args:
        storage_manager: StorageManager instance
        camera_name: Optional camera name to filter by
        dry_run: If True, only show what would be done without making changes
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting video reindexing (dry_run={dry_run})")
    if camera_name:
        logger.info(f"Filtering by camera: {camera_name}")
    
    # Get all video files
    files = storage_manager.get_recording_files(camera_name=camera_name)
    
    unknown_files = [f for f in files if f.get("status") == "unknown"]
    
    if not unknown_files:
        logger.info("No files with 'unknown' status found")
        return
    
    logger.info(f"Found {len(unknown_files)} files with 'unknown' status")
    
    updated_count = 0
    
    for file_info in unknown_files:
        file_id = file_info["file_id"]
        filename = file_info["filename"]
        
        logger.info(f"Processing: {file_id}")
        logger.info(f"  File: {filename}")
        logger.info(f"  Current status: {file_info['status']}")
        
        if not dry_run:
            # Update the file index directly
            if file_id not in storage_manager.file_index["files"]:
                # File is not in index, add it
                file_path = Path(filename)
                if file_path.exists():
                    stat = file_path.stat()
                    file_mtime = datetime.fromtimestamp(stat.st_mtime)
                    
                    new_file_info = {
                        "camera_name": file_info["camera_name"],
                        "filename": filename,
                        "file_id": file_id,
                        "start_time": file_mtime.isoformat(),
                        "end_time": file_mtime.isoformat(),  # Use file mtime as end time
                        "file_size_bytes": stat.st_size,
                        "duration_seconds": None,  # Will be extracted later if needed
                        "machine_trigger": None,
                        "status": "completed",  # Set to completed
                        "created_at": file_mtime.isoformat()
                    }
                    
                    storage_manager.file_index["files"][file_id] = new_file_info
                    logger.info(f"  Added to index with status: completed")
                    updated_count += 1
                else:
                    logger.warning(f"  File does not exist: {filename}")
            else:
                # File is in index but has unknown status, update it
                storage_manager.file_index["files"][file_id]["status"] = "completed"
                logger.info(f"  Updated status to: completed")
                updated_count += 1
        else:
            logger.info(f"  Would update status to: completed")
            updated_count += 1
    
    if not dry_run and updated_count > 0:
        # Save the updated index
        storage_manager._save_file_index()
        logger.info(f"Saved updated file index")
    
    logger.info(f"Reindexing complete: {updated_count} files {'would be ' if dry_run else ''}updated")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Reindex video files with unknown status")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without making changes")
    parser.add_argument("--camera", type=str, 
                       help="Only process files for specific camera")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Set logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize system components
        logger.info("Initializing USDA Vision Camera System components...")
        
        config = Config()
        state_manager = StateManager()
        storage_manager = StorageManager(config, state_manager)
        
        logger.info("Components initialized successfully")
        
        # Run reindexing
        reindex_videos(
            storage_manager=storage_manager,
            camera_name=args.camera,
            dry_run=args.dry_run
        )
        
        if args.dry_run:
            logger.info("Dry run completed. Use --no-dry-run to apply changes.")
        else:
            logger.info("Reindexing completed successfully!")
            logger.info("Videos should now be streamable through the API.")
        
    except Exception as e:
        logger.error(f"Error during reindexing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
