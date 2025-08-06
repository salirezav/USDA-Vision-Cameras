"""
USDA Vision Camera System - Core Module

This module contains the core functionality for the USDA vision camera system,
including configuration management, state management, and event handling.
"""

__version__ = "1.0.0"
__author__ = "USDA Vision Team"

from .config import Config
from .state_manager import StateManager
from .events import EventSystem

__all__ = ["Config", "StateManager", "EventSystem"]
