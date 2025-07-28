"""
SDK Configuration for the USDA Vision Camera System.

This module handles SDK initialization and configuration to suppress error messages.
"""

import sys
import os
import logging

# Add python demo to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "python demo"))
import mvsdk

logger = logging.getLogger(__name__)

# Global flag to track SDK initialization
_sdk_initialized = False


def initialize_sdk_with_suppression():
    """Initialize the camera SDK with error suppression"""
    global _sdk_initialized
    
    if _sdk_initialized:
        return True
    
    try:
        # Initialize SDK with English language
        result = mvsdk.CameraSdkInit(1)
        if result == 0:
            logger.info("Camera SDK initialized successfully")
            
            # Try to set system options to suppress logging
            try:
                # These are common options that might control logging
                # We'll try them and ignore failures since they might not be supported
                
                # Try to disable debug output
                try:
                    mvsdk.CameraSetSysOption("DebugLevel", "0")
                except:
                    pass
                
                # Try to disable console output
                try:
                    mvsdk.CameraSetSysOption("ConsoleOutput", "0")
                except:
                    pass
                
                # Try to disable error logging
                try:
                    mvsdk.CameraSetSysOption("ErrorLog", "0")
                except:
                    pass
                
                # Try to set log level to none
                try:
                    mvsdk.CameraSetSysOption("LogLevel", "0")
                except:
                    pass
                
                # Try to disable verbose mode
                try:
                    mvsdk.CameraSetSysOption("Verbose", "0")
                except:
                    pass
                
                logger.debug("Attempted to configure SDK logging options")
                
            except Exception as e:
                logger.debug(f"Could not configure SDK logging options: {e}")
            
            _sdk_initialized = True
            return True
        else:
            logger.error(f"SDK initialization failed with code: {result}")
            return False
            
    except Exception as e:
        logger.error(f"SDK initialization failed: {e}")
        return False


def ensure_sdk_initialized():
    """Ensure the SDK is initialized before camera operations"""
    if not _sdk_initialized:
        return initialize_sdk_with_suppression()
    return True
