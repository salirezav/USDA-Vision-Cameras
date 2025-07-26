"""
USDA Vision Camera System

A comprehensive system for monitoring machines via MQTT and automatically recording
video from GigE cameras when machines are active.
"""

__version__ = "1.0.0"
__author__ = "USDA Vision Team"

from .main import USDAVisionSystem

__all__ = ["USDAVisionSystem"]
