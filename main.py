#!/usr/bin/env python3
"""
Main entry point for the USDA Vision Camera System.

This script starts the complete system including MQTT monitoring, camera management,
and video recording based on machine state changes.
"""

import sys
import os

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from usda_vision_system.main import main

if __name__ == "__main__":
    main()
