#!/usr/bin/env python3
"""
Test script for camera streaming functionality.

This script tests the new streaming capabilities without interfering with recording.
"""

import sys
import os
import time
import requests
import threading
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_endpoints():
    """Test the streaming API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Camera Streaming API Endpoints")
    print("=" * 50)
    
    # Test system status
    try:
        response = requests.get(f"{base_url}/system/status", timeout=5)
        if response.status_code == 200:
            print("✅ System status endpoint working")
            data = response.json()
            print(f"   System: {data.get('status', 'Unknown')}")
            print(f"   Camera Manager: {'Running' if data.get('camera_manager_running') else 'Stopped'}")
        else:
            print(f"❌ System status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ System status endpoint error: {e}")
    
    # Test camera list
    try:
        response = requests.get(f"{base_url}/cameras", timeout=5)
        if response.status_code == 200:
            print("✅ Camera list endpoint working")
            cameras = response.json()
            print(f"   Found {len(cameras)} cameras: {list(cameras.keys())}")
            
            # Test streaming for each camera
            for camera_name in cameras.keys():
                test_camera_streaming(base_url, camera_name)
                
        else:
            print(f"❌ Camera list endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Camera list endpoint error: {e}")

def test_camera_streaming(base_url, camera_name):
    """Test streaming for a specific camera"""
    print(f"\n🎥 Testing streaming for {camera_name}")
    print("-" * 30)
    
    # Test start streaming
    try:
        response = requests.post(f"{base_url}/cameras/{camera_name}/start-stream", timeout=10)
        if response.status_code == 200:
            print(f"✅ Start stream endpoint working for {camera_name}")
            data = response.json()
            print(f"   Response: {data.get('message', 'No message')}")
        else:
            print(f"❌ Start stream failed for {camera_name}: {response.status_code}")
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Start stream error for {camera_name}: {e}")
        return
    
    # Wait a moment for stream to initialize
    time.sleep(2)
    
    # Test stream endpoint (just check if it responds)
    try:
        response = requests.get(f"{base_url}/cameras/{camera_name}/stream", timeout=5, stream=True)
        if response.status_code == 200:
            print(f"✅ Stream endpoint responding for {camera_name}")
            print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
            
            # Read a small amount of data to verify it's working
            chunk_count = 0
            for chunk in response.iter_content(chunk_size=1024):
                chunk_count += 1
                if chunk_count >= 3:  # Read a few chunks then stop
                    break
            
            print(f"   Received {chunk_count} data chunks")
        else:
            print(f"❌ Stream endpoint failed for {camera_name}: {response.status_code}")
    except Exception as e:
        print(f"❌ Stream endpoint error for {camera_name}: {e}")
    
    # Test stop streaming
    try:
        response = requests.post(f"{base_url}/cameras/{camera_name}/stop-stream", timeout=5)
        if response.status_code == 200:
            print(f"✅ Stop stream endpoint working for {camera_name}")
            data = response.json()
            print(f"   Response: {data.get('message', 'No message')}")
        else:
            print(f"❌ Stop stream failed for {camera_name}: {response.status_code}")
    except Exception as e:
        print(f"❌ Stop stream error for {camera_name}: {e}")

def test_concurrent_recording_and_streaming():
    """Test that streaming doesn't interfere with recording"""
    base_url = "http://localhost:8000"
    
    print("\n🔄 Testing Concurrent Recording and Streaming")
    print("=" * 50)
    
    try:
        # Get available cameras
        response = requests.get(f"{base_url}/cameras", timeout=5)
        if response.status_code != 200:
            print("❌ Cannot get camera list for concurrent test")
            return
        
        cameras = response.json()
        if not cameras:
            print("❌ No cameras available for concurrent test")
            return
        
        camera_name = list(cameras.keys())[0]  # Use first camera
        print(f"Using camera: {camera_name}")
        
        # Start streaming
        print("1. Starting streaming...")
        response = requests.post(f"{base_url}/cameras/{camera_name}/start-stream", timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to start streaming: {response.text}")
            return
        
        time.sleep(2)
        
        # Start recording
        print("2. Starting recording...")
        response = requests.post(f"{base_url}/cameras/{camera_name}/start-recording", 
                               json={"filename": "test_concurrent_recording.avi"}, timeout=10)
        if response.status_code == 200:
            print("✅ Recording started successfully while streaming")
        else:
            print(f"❌ Failed to start recording while streaming: {response.text}")
        
        # Let both run for a few seconds
        print("3. Running both streaming and recording for 5 seconds...")
        time.sleep(5)
        
        # Stop recording
        print("4. Stopping recording...")
        response = requests.post(f"{base_url}/cameras/{camera_name}/stop-recording", timeout=5)
        if response.status_code == 200:
            print("✅ Recording stopped successfully")
        else:
            print(f"❌ Failed to stop recording: {response.text}")
        
        # Stop streaming
        print("5. Stopping streaming...")
        response = requests.post(f"{base_url}/cameras/{camera_name}/stop-stream", timeout=5)
        if response.status_code == 200:
            print("✅ Streaming stopped successfully")
        else:
            print(f"❌ Failed to stop streaming: {response.text}")
        
        print("✅ Concurrent test completed successfully!")
        
    except Exception as e:
        print(f"❌ Concurrent test error: {e}")

def main():
    """Main test function"""
    print("🚀 USDA Vision Camera Streaming Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Wait for system to be ready
    print("⏳ Waiting for system to be ready...")
    time.sleep(3)
    
    # Run tests
    test_api_endpoints()
    test_concurrent_recording_and_streaming()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    print("\n📋 Next Steps:")
    print("1. Open camera_preview.html in your browser")
    print("2. Click 'Start Stream' for any camera")
    print("3. Verify live preview works without blocking recording")
    print("4. Test concurrent recording and streaming")

if __name__ == "__main__":
    main()
