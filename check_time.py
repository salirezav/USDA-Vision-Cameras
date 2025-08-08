#!/usr/bin/env python3
"""
Time verification script for USDA Vision Camera System
Checks if system time is properly synchronized
"""

import datetime
import pytz
import requests
import json

def check_system_time():
    """Check system time against multiple sources"""
    print("🕐 USDA Vision Camera System - Time Verification")
    print("=" * 50)
    
    # Get local time
    local_time = datetime.datetime.now()
    utc_time = datetime.datetime.utcnow()
    
    # Get Atlanta timezone
    atlanta_tz = pytz.timezone('America/New_York')
    atlanta_time = datetime.datetime.now(atlanta_tz)
    
    print(f"Local system time: {local_time}")
    print(f"UTC time: {utc_time}")
    print(f"Atlanta time: {atlanta_time}")
    print(f"Timezone: {atlanta_time.tzname()}")
    
    # Check against world time API
    try:
        print("\n🌐 Checking against world time API...")
        response = requests.get("http://worldtimeapi.org/api/timezone/America/New_York", timeout=5)
        if response.status_code == 200:
            data = response.json()
            api_time = datetime.datetime.fromisoformat(data['datetime'].replace('Z', '+00:00'))
            
            # Compare times (allow 5 second difference)
            time_diff = abs((atlanta_time.replace(tzinfo=None) - api_time.replace(tzinfo=None)).total_seconds())
            
            print(f"API time: {api_time}")
            print(f"Time difference: {time_diff:.2f} seconds")
            
            if time_diff < 5:
                print("✅ Time is synchronized (within 5 seconds)")
                return True
            else:
                print("❌ Time is NOT synchronized (difference > 5 seconds)")
                return False
        else:
            print("⚠️  Could not reach time API")
            return None
    except Exception as e:
        print(f"⚠️  Error checking time API: {e}")
        return None

if __name__ == "__main__":
    check_system_time()
