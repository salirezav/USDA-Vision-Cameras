"""
Logging configuration for the USDA Vision Camera System.

This module provides comprehensive logging setup with rotation, formatting,
and different log levels for different components.
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class USDAVisionLogger:
    """Custom logger setup for the USDA Vision Camera System"""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None, 
                 enable_console: bool = True, enable_rotation: bool = True):
        self.log_level = log_level.upper()
        self.log_file = log_file
        self.enable_console = enable_console
        self.enable_rotation = enable_rotation
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup comprehensive logging configuration"""
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        colored_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.log_level))
            console_handler.setFormatter(colored_formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if self.log_file:
            try:
                # Create log directory if it doesn't exist
                log_dir = os.path.dirname(self.log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                if self.enable_rotation:
                    # Rotating file handler (10MB max, keep 5 backups)
                    file_handler = logging.handlers.RotatingFileHandler(
                        self.log_file,
                        maxBytes=10*1024*1024,  # 10MB
                        backupCount=5
                    )
                else:
                    file_handler = logging.FileHandler(self.log_file)
                
                file_handler.setLevel(logging.DEBUG)  # File gets all messages
                file_handler.setFormatter(detailed_formatter)
                root_logger.addHandler(file_handler)
                
            except Exception as e:
                print(f"Warning: Could not setup file logging: {e}")
        
        # Setup specific logger levels for different components
        self._setup_component_loggers()
        
        # Log the logging setup
        logger = logging.getLogger(__name__)
        logger.info(f"Logging initialized - Level: {self.log_level}, File: {self.log_file}")
    
    def _setup_component_loggers(self) -> None:
        """Setup specific log levels for different components"""
        
        # MQTT client - can be verbose
        mqtt_logger = logging.getLogger('usda_vision_system.mqtt')
        if self.log_level == 'DEBUG':
            mqtt_logger.setLevel(logging.DEBUG)
        else:
            mqtt_logger.setLevel(logging.INFO)
        
        # Camera components - important for debugging
        camera_logger = logging.getLogger('usda_vision_system.camera')
        camera_logger.setLevel(logging.INFO)
        
        # API server - can be noisy
        api_logger = logging.getLogger('usda_vision_system.api')
        if self.log_level == 'DEBUG':
            api_logger.setLevel(logging.DEBUG)
        else:
            api_logger.setLevel(logging.INFO)
        
        # Uvicorn - reduce noise unless debugging
        uvicorn_logger = logging.getLogger('uvicorn')
        if self.log_level == 'DEBUG':
            uvicorn_logger.setLevel(logging.INFO)
        else:
            uvicorn_logger.setLevel(logging.WARNING)
        
        # FastAPI - reduce noise
        fastapi_logger = logging.getLogger('fastapi')
        fastapi_logger.setLevel(logging.WARNING)
    
    @staticmethod
    def setup_exception_logging():
        """Setup logging for uncaught exceptions"""
        
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                # Don't log keyboard interrupts
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            logger = logging.getLogger("uncaught_exception")
            logger.critical(
                "Uncaught exception",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
        
        sys.excepthook = handle_exception


class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(f"performance.{name}")
        self.start_time: Optional[float] = None
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation"""
        import time
        self.start_time = time.time()
        self.logger.debug(f"Started: {operation}")
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and log duration"""
        import time
        if self.start_time is None:
            self.logger.warning(f"Timer not started for: {operation}")
            return 0.0
        
        duration = time.time() - self.start_time
        self.logger.info(f"Completed: {operation} in {duration:.3f}s")
        self.start_time = None
        return duration
    
    def log_metric(self, metric_name: str, value: float, unit: str = "") -> None:
        """Log a performance metric"""
        self.logger.info(f"Metric: {metric_name} = {value} {unit}")


class ErrorTracker:
    """Track and log errors with context"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = logging.getLogger(f"errors.{component_name}")
        self.error_count = 0
        self.last_error_time: Optional[datetime] = None
    
    def log_error(self, error: Exception, context: str = "", 
                  additional_data: Optional[dict] = None) -> None:
        """Log an error with context and tracking"""
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        error_msg = f"Error in {self.component_name}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        if additional_data:
            error_msg += f" | Data: {additional_data}"
        
        self.logger.error(error_msg, exc_info=True)
    
    def log_warning(self, message: str, context: str = "") -> None:
        """Log a warning with context"""
        warning_msg = f"Warning in {self.component_name}"
        if context:
            warning_msg += f" ({context})"
        warning_msg += f": {message}"
        
        self.logger.warning(warning_msg)
    
    def get_error_stats(self) -> dict:
        """Get error statistics"""
        return {
            "component": self.component_name,
            "error_count": self.error_count,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None
        }


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> USDAVisionLogger:
    """Setup logging for the entire application"""
    
    # Setup main logging
    logger_setup = USDAVisionLogger(
        log_level=log_level,
        log_file=log_file,
        enable_console=True,
        enable_rotation=True
    )
    
    # Setup exception logging
    USDAVisionLogger.setup_exception_logging()
    
    return logger_setup


def get_performance_logger(component_name: str) -> PerformanceLogger:
    """Get a performance logger for a component"""
    return PerformanceLogger(component_name)


def get_error_tracker(component_name: str) -> ErrorTracker:
    """Get an error tracker for a component"""
    return ErrorTracker(component_name)
