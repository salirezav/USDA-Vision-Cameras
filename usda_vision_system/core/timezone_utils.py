"""
Timezone utilities for the USDA Vision Camera System.

This module provides timezone-aware datetime handling for Atlanta, Georgia.
"""

import datetime
import pytz
import logging
from typing import Optional


class TimezoneManager:
    """Manages timezone-aware datetime operations"""
    
    def __init__(self, timezone_name: str = "America/New_York"):
        self.timezone_name = timezone_name
        self.timezone = pytz.timezone(timezone_name)
        self.logger = logging.getLogger(__name__)
        
        # Log timezone information
        self.logger.info(f"Timezone manager initialized for {timezone_name}")
        self._log_timezone_info()
    
    def _log_timezone_info(self) -> None:
        """Log current timezone information"""
        now = self.now()
        self.logger.info(f"Current local time: {now}")
        self.logger.info(f"Current UTC time: {self.to_utc(now)}")
        self.logger.info(f"Timezone: {now.tzname()} (UTC{now.strftime('%z')})")
    
    def now(self) -> datetime.datetime:
        """Get current time in the configured timezone"""
        return datetime.datetime.now(self.timezone)
    
    def utc_now(self) -> datetime.datetime:
        """Get current UTC time"""
        return datetime.datetime.now(pytz.UTC)
    
    def to_local(self, dt: datetime.datetime) -> datetime.datetime:
        """Convert datetime to local timezone"""
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = pytz.UTC.localize(dt)
        return dt.astimezone(self.timezone)
    
    def to_utc(self, dt: datetime.datetime) -> datetime.datetime:
        """Convert datetime to UTC"""
        if dt.tzinfo is None:
            # Assume local timezone if no timezone info
            dt = self.timezone.localize(dt)
        return dt.astimezone(pytz.UTC)
    
    def localize(self, dt: datetime.datetime) -> datetime.datetime:
        """Add timezone info to naive datetime (assumes local timezone)"""
        if dt.tzinfo is not None:
            return dt
        return self.timezone.localize(dt)
    
    def format_timestamp(self, dt: Optional[datetime.datetime] = None, 
                        include_timezone: bool = True) -> str:
        """Format datetime as timestamp string"""
        if dt is None:
            dt = self.now()
        
        if dt.tzinfo is None:
            dt = self.localize(dt)
        
        if include_timezone:
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def format_filename_timestamp(self, dt: Optional[datetime.datetime] = None) -> str:
        """Format datetime for use in filenames (no special characters)"""
        if dt is None:
            dt = self.now()
        
        if dt.tzinfo is None:
            dt = self.localize(dt)
        
        return dt.strftime("%Y%m%d_%H%M%S")
    
    def parse_timestamp(self, timestamp_str: str) -> datetime.datetime:
        """Parse timestamp string to datetime"""
        try:
            # Try parsing with timezone info
            return datetime.datetime.fromisoformat(timestamp_str)
        except ValueError:
            try:
                # Try parsing without timezone (assume local)
                dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                return self.localize(dt)
            except ValueError:
                try:
                    # Try parsing filename format
                    dt = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    return self.localize(dt)
                except ValueError:
                    raise ValueError(f"Unable to parse timestamp: {timestamp_str}")
    
    def is_dst(self, dt: Optional[datetime.datetime] = None) -> bool:
        """Check if datetime is during daylight saving time"""
        if dt is None:
            dt = self.now()
        
        if dt.tzinfo is None:
            dt = self.localize(dt)
        
        return bool(dt.dst())
    
    def get_timezone_offset(self, dt: Optional[datetime.datetime] = None) -> str:
        """Get timezone offset string (e.g., '-0500' or '-0400')"""
        if dt is None:
            dt = self.now()
        
        if dt.tzinfo is None:
            dt = self.localize(dt)
        
        return dt.strftime('%z')
    
    def get_timezone_name(self, dt: Optional[datetime.datetime] = None) -> str:
        """Get timezone name (e.g., 'EST' or 'EDT')"""
        if dt is None:
            dt = self.now()
        
        if dt.tzinfo is None:
            dt = self.localize(dt)
        
        return dt.tzname()


# Global timezone manager instance for Atlanta, Georgia
atlanta_tz = TimezoneManager("America/New_York")


# Convenience functions
def now_atlanta() -> datetime.datetime:
    """Get current Atlanta time"""
    return atlanta_tz.now()


def format_atlanta_timestamp(dt: Optional[datetime.datetime] = None) -> str:
    """Format timestamp in Atlanta timezone"""
    return atlanta_tz.format_timestamp(dt)


def format_filename_timestamp(dt: Optional[datetime.datetime] = None) -> str:
    """Format timestamp for filenames"""
    return atlanta_tz.format_filename_timestamp(dt)


def to_atlanta_time(dt: datetime.datetime) -> datetime.datetime:
    """Convert any datetime to Atlanta time"""
    return atlanta_tz.to_local(dt)


def check_time_sync() -> dict:
    """Check if system time appears to be synchronized"""
    import requests
    
    result = {
        "system_time": now_atlanta(),
        "timezone": atlanta_tz.get_timezone_name(),
        "offset": atlanta_tz.get_timezone_offset(),
        "dst": atlanta_tz.is_dst(),
        "sync_status": "unknown",
        "time_diff_seconds": None,
        "error": None
    }
    
    try:
        # Check against world time API
        response = requests.get(
            "http://worldtimeapi.org/api/timezone/America/New_York", 
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            api_time = datetime.datetime.fromisoformat(data['datetime'])
            
            # Convert to same timezone for comparison
            system_time = atlanta_tz.now()
            time_diff = abs((system_time.replace(tzinfo=None) - 
                           api_time.replace(tzinfo=None)).total_seconds())
            
            result["api_time"] = api_time
            result["time_diff_seconds"] = time_diff
            
            if time_diff < 5:
                result["sync_status"] = "synchronized"
            elif time_diff < 30:
                result["sync_status"] = "minor_drift"
            else:
                result["sync_status"] = "out_of_sync"
        else:
            result["error"] = f"API returned status {response.status_code}"
            
    except Exception as e:
        result["error"] = str(e)
    
    return result


def log_time_info(logger: Optional[logging.Logger] = None) -> None:
    """Log comprehensive time information"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    sync_info = check_time_sync()
    
    logger.info("=== TIME SYNCHRONIZATION STATUS ===")
    logger.info(f"System time: {sync_info['system_time']}")
    logger.info(f"Timezone: {sync_info['timezone']} ({sync_info['offset']})")
    logger.info(f"Daylight Saving: {'Yes' if sync_info['dst'] else 'No'}")
    logger.info(f"Sync status: {sync_info['sync_status']}")
    
    if sync_info.get('time_diff_seconds') is not None:
        logger.info(f"Time difference: {sync_info['time_diff_seconds']:.2f} seconds")
    
    if sync_info.get('error'):
        logger.warning(f"Time sync check error: {sync_info['error']}")
    
    logger.info("=====================================")
