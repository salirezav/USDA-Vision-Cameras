#!/usr/bin/env python3
"""
Test script for camera recovery API endpoints.

This script tests the new camera recovery functionality without requiring actual cameras.
"""

import requests
import json
import time
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Test an API endpoint and return the response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data or {}, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"\n{method} {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"Response: {response.text}")
            return {"text": response.text}
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - API server not running at {BASE_URL}")
        return {"error": "connection_failed"}
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout")
        return {"error": "timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

def main():
    """Test camera recovery API endpoints"""
    print("🔧 Testing Camera Recovery API Endpoints")
    print("=" * 50)
    
    # Test basic endpoints first
    print("\n📋 BASIC API TESTS")
    test_endpoint("GET", "/health")
    test_endpoint("GET", "/cameras")
    
    # Test camera recovery endpoints
    print("\n🔧 CAMERA RECOVERY TESTS")
    
    camera_names = ["camera1", "camera2"]
    
    for camera_name in camera_names:
        print(f"\n--- Testing {camera_name} ---")
        
        # Test connection
        test_endpoint("POST", f"/cameras/{camera_name}/test-connection")
        
        # Test reconnect
        test_endpoint("POST", f"/cameras/{camera_name}/reconnect")
        
        # Test restart grab
        test_endpoint("POST", f"/cameras/{camera_name}/restart-grab")
        
        # Test reset timestamp
        test_endpoint("POST", f"/cameras/{camera_name}/reset-timestamp")
        
        # Test full reset
        test_endpoint("POST", f"/cameras/{camera_name}/full-reset")
        
        # Test reinitialize
        test_endpoint("POST", f"/cameras/{camera_name}/reinitialize")
        
        time.sleep(0.5)  # Small delay between tests
    
    print("\n✅ Camera recovery API tests completed!")
    print("\nNote: Some operations may fail if cameras are not connected,")
    print("but the API endpoints should respond with proper error messages.")

if __name__ == "__main__":
    main()
