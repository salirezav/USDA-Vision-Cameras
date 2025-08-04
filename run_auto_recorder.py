#!/usr/bin/env python3
"""
Service script to run the standalone auto-recorder

Usage:
    sudo python run_auto_recorder.py
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from usda_vision_system.recording.standalone_auto_recorder import StandaloneAutoRecorder


def main():
    """Main entry point"""
    print("🚀 Starting USDA Vision Auto-Recorder Service")
    
    # Check if running as root
    if os.geteuid() != 0:
        print("❌ This script must be run as root (use sudo)")
        print("   sudo python run_auto_recorder.py")
        sys.exit(1)
    
    # Create and run auto-recorder
    recorder = StandaloneAutoRecorder()
    recorder.run()


if __name__ == "__main__":
    main()
