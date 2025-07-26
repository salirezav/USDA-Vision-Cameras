"""
API module for the USDA Vision Camera System.

This module provides REST API endpoints and WebSocket support for dashboard integration.
"""

from .server import APIServer
from .models import *

__all__ = ["APIServer"]
