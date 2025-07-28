#!/usr/bin/env python3
"""
Test script to verify the API changes for camera settings and filename handling.
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_api_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint and return the response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        
        print(f"\n{method} {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {url}")
        print("Make sure the API server is running with: python main.py")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_camera_recording_with_settings():
    """Test camera recording with new settings parameters"""
    
    print("=" * 60)
    print("Testing Camera Recording API with New Settings")
    print("=" * 60)
    
    # Test 1: Basic recording without settings
    print("\n1. Testing basic recording (no settings)")
    basic_request = {
        "camera_name": "camera1",
        "filename": "test_basic.avi"
    }
    
    result = test_api_endpoint("/cameras/camera1/start-recording", "POST", basic_request)
    if result and result.get("success"):
        print("✅ Basic recording started successfully")
        print(f"   Filename: {result.get('filename')}")
        
        # Stop recording
        time.sleep(2)
        test_api_endpoint("/cameras/camera1/stop-recording", "POST")
    else:
        print("❌ Basic recording failed")
    
    # Test 2: Recording with camera settings
    print("\n2. Testing recording with camera settings")
    settings_request = {
        "camera_name": "camera1",
        "filename": "test_with_settings.avi",
        "exposure_ms": 2.0,
        "gain": 4.0,
        "fps": 5.0
    }
    
    result = test_api_endpoint("/cameras/camera1/start-recording", "POST", settings_request)
    if result and result.get("success"):
        print("✅ Recording with settings started successfully")
        print(f"   Filename: {result.get('filename')}")
        
        # Stop recording
        time.sleep(2)
        test_api_endpoint("/cameras/camera1/stop-recording", "POST")
    else:
        print("❌ Recording with settings failed")
    
    # Test 3: Recording with only settings (no filename)
    print("\n3. Testing recording with settings only (no filename)")
    settings_only_request = {
        "camera_name": "camera1",
        "exposure_ms": 1.5,
        "gain": 3.0,
        "fps": 7.0
    }
    
    result = test_api_endpoint("/cameras/camera1/start-recording", "POST", settings_only_request)
    if result and result.get("success"):
        print("✅ Recording with settings only started successfully")
        print(f"   Filename: {result.get('filename')}")
        
        # Stop recording
        time.sleep(2)
        test_api_endpoint("/cameras/camera1/stop-recording", "POST")
    else:
        print("❌ Recording with settings only failed")
    
    # Test 4: Test filename datetime prefix
    print("\n4. Testing filename datetime prefix")
    timestamp_before = datetime.now().strftime("%Y%m%d_%H%M")
    
    filename_test_request = {
        "camera_name": "camera1",
        "filename": "my_custom_name.avi"
    }
    
    result = test_api_endpoint("/cameras/camera1/start-recording", "POST", filename_test_request)
    if result and result.get("success"):
        returned_filename = result.get('filename', '')
        print(f"   Original filename: my_custom_name.avi")
        print(f"   Returned filename: {returned_filename}")
        
        # Check if datetime prefix was added
        if timestamp_before in returned_filename and "my_custom_name.avi" in returned_filename:
            print("✅ Datetime prefix correctly added to filename")
        else:
            print("❌ Datetime prefix not properly added")
        
        # Stop recording
        time.sleep(2)
        test_api_endpoint("/cameras/camera1/stop-recording", "POST")
    else:
        print("❌ Filename test failed")

def test_system_status():
    """Test basic system status to ensure API is working"""
    print("\n" + "=" * 60)
    print("Testing System Status")
    print("=" * 60)
    
    # Test system status
    result = test_api_endpoint("/system/status")
    if result:
        print("✅ System status API working")
        print(f"   System started: {result.get('system_started')}")
        print(f"   MQTT connected: {result.get('mqtt_connected')}")
    else:
        print("❌ System status API failed")
    
    # Test camera status
    result = test_api_endpoint("/cameras")
    if result:
        print("✅ Camera status API working")
        for camera_name, camera_info in result.items():
            print(f"   {camera_name}: {camera_info.get('status')}")
    else:
        print("❌ Camera status API failed")

if __name__ == "__main__":
    print("USDA Vision Camera System - API Changes Test")
    print("This script tests the new camera settings parameters and filename handling")
    print("\nMake sure the system is running with: python main.py")
    
    # Test system status first
    test_system_status()
    
    # Test camera recording with new features
    test_camera_recording_with_settings()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
