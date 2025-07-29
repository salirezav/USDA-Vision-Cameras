#!/usr/bin/env python3
"""
Test script to demonstrate maximum FPS capture functionality.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_fps_modes():
    """Test different FPS modes to demonstrate the functionality"""
    
    print("=" * 60)
    print("Testing Maximum FPS Capture Functionality")
    print("=" * 60)
    
    # Test configurations
    test_configs = [
        {
            "name": "Normal FPS (3.0)",
            "data": {
                "filename": "normal_fps_test.avi",
                "exposure_ms": 1.0,
                "gain": 3.0,
                "fps": 3.0
            }
        },
        {
            "name": "High FPS (10.0)",
            "data": {
                "filename": "high_fps_test.avi", 
                "exposure_ms": 0.5,
                "gain": 2.0,
                "fps": 10.0
            }
        },
        {
            "name": "Maximum FPS (fps=0)",
            "data": {
                "filename": "max_fps_test.avi",
                "exposure_ms": 0.1,  # Very short exposure for max speed
                "gain": 1.0,         # Low gain to avoid overexposure
                "fps": 0             # Maximum speed - no delay
            }
        },
        {
            "name": "Default FPS (omitted)",
            "data": {
                "filename": "default_fps_test.avi",
                "exposure_ms": 1.0,
                "gain": 3.0
                # fps omitted - uses camera config default
            }
        }
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n{i}. Testing {config['name']}")
        print("-" * 40)
        
        # Start recording
        try:
            response = requests.post(
                f"{BASE_URL}/cameras/camera1/start-recording",
                json=config['data'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Recording started successfully")
                    print(f"   Filename: {result.get('filename')}")
                    print(f"   Settings: {json.dumps(config['data'], indent=6)}")
                    
                    # Record for a short time
                    print(f"   Recording for 3 seconds...")
                    time.sleep(3)
                    
                    # Stop recording
                    stop_response = requests.post(f"{BASE_URL}/cameras/camera1/stop-recording")
                    if stop_response.status_code == 200:
                        stop_result = stop_response.json()
                        if stop_result.get('success'):
                            print(f"✅ Recording stopped successfully")
                            if 'duration_seconds' in stop_result:
                                print(f"   Duration: {stop_result['duration_seconds']:.1f}s")
                        else:
                            print(f"❌ Failed to stop recording: {stop_result.get('message')}")
                    else:
                        print(f"❌ Stop request failed: {stop_response.status_code}")
                        
                else:
                    print(f"❌ Recording failed: {result.get('message')}")
            else:
                print(f"❌ Request failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Could not connect to {BASE_URL}")
            print("Make sure the API server is running with: python main.py")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Wait between tests
        if i < len(test_configs):
            print("   Waiting 2 seconds before next test...")
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("FPS Test Summary:")
    print("=" * 60)
    print("• fps > 0: Controlled frame rate with sleep delay")
    print("• fps = 0: MAXIMUM speed capture (no delay between frames)")
    print("• fps omitted: Uses camera config default")
    print("• Video files with fps=0 are saved with 30 FPS metadata")
    print("• Actual capture rate with fps=0 depends on:")
    print("  - Camera hardware capabilities")
    print("  - Exposure time (shorter = faster)")
    print("  - Processing overhead")
    print("=" * 60)

if __name__ == "__main__":
    print("USDA Vision Camera System - Maximum FPS Test")
    print("This script demonstrates fps=0 for maximum capture speed")
    print("\nMake sure the system is running with: python main.py")
    
    test_fps_modes()
