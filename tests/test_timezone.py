#!/usr/bin/env python3
"""
Test timezone functionality for the USDA Vision Camera System.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from usda_vision_system.core.timezone_utils import (
    now_atlanta, format_atlanta_timestamp, format_filename_timestamp,
    check_time_sync, log_time_info
)
import logging

def test_timezone_functions():
    """Test timezone utility functions"""
    print("🕐 Testing USDA Vision Camera System Timezone Functions")
    print("=" * 60)
    
    # Test current time functions
    atlanta_time = now_atlanta()
    print(f"Current Atlanta time: {atlanta_time}")
    print(f"Timezone: {atlanta_time.tzname()}")
    print(f"UTC offset: {atlanta_time.strftime('%z')}")
    
    # Test timestamp formatting
    timestamp_str = format_atlanta_timestamp()
    filename_str = format_filename_timestamp()
    
    print(f"\nTimestamp formats:")
    print(f"  Display format: {timestamp_str}")
    print(f"  Filename format: {filename_str}")
    
    # Test time sync
    print(f"\n🔄 Testing time synchronization...")
    sync_info = check_time_sync()
    print(f"Sync status: {sync_info['sync_status']}")
    if sync_info.get('time_diff_seconds') is not None:
        print(f"Time difference: {sync_info['time_diff_seconds']:.2f} seconds")
    
    # Test logging
    print(f"\n📝 Testing time logging...")
    logging.basicConfig(level=logging.INFO)
    log_time_info()
    
    print(f"\n✅ All timezone tests completed successfully!")
    
    # Show example filename that would be generated
    example_filename = f"camera1_recording_{filename_str}.avi"
    print(f"\nExample recording filename: {example_filename}")

if __name__ == "__main__":
    test_timezone_functions()
