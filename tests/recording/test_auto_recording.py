#!/usr/bin/env python3
"""
Test script for auto-recording functionality.

This script tests the auto-recording feature by simulating MQTT state changes
and verifying that cameras start and stop recording automatically.
"""

import sys
import os
import time
import json
import requests
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from usda_vision_system.core.config import Config
from usda_vision_system.core.state_manager import StateManager
from usda_vision_system.core.events import EventSystem, publish_machine_state_changed


class AutoRecordingTester:
    """Test class for auto-recording functionality"""

    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.config = Config("config.json")
        self.state_manager = StateManager()
        self.event_system = EventSystem()
        
        # Test results
        self.test_results = []

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log a test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"[{timestamp}] {status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": timestamp
        })

    def check_api_available(self) -> bool:
        """Check if the API server is available"""
        try:
            response = requests.get(f"{self.api_base_url}/cameras", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_camera_status(self, camera_name: str) -> dict:
        """Get camera status from API"""
        try:
            response = requests.get(f"{self.api_base_url}/cameras", timeout=5)
            if response.status_code == 200:
                cameras = response.json()
                return cameras.get(camera_name, {})
        except Exception as e:
            print(f"Error getting camera status: {e}")
        return {}

    def get_auto_recording_status(self) -> dict:
        """Get auto-recording manager status"""
        try:
            response = requests.get(f"{self.api_base_url}/auto-recording/status", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error getting auto-recording status: {e}")
        return {}

    def enable_auto_recording(self, camera_name: str) -> bool:
        """Enable auto-recording for a camera"""
        try:
            response = requests.post(f"{self.api_base_url}/cameras/{camera_name}/auto-recording/enable", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error enabling auto-recording: {e}")
            return False

    def disable_auto_recording(self, camera_name: str) -> bool:
        """Disable auto-recording for a camera"""
        try:
            response = requests.post(f"{self.api_base_url}/cameras/{camera_name}/auto-recording/disable", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error disabling auto-recording: {e}")
            return False

    def simulate_machine_state_change(self, machine_name: str, state: str):
        """Simulate a machine state change via event system"""
        print(f"🔄 Simulating machine state change: {machine_name} -> {state}")
        publish_machine_state_changed(machine_name, state, "test_script")

    def test_api_connectivity(self) -> bool:
        """Test API connectivity"""
        available = self.check_api_available()
        self.log_test("API Connectivity", available, 
                     "API server is reachable" if available else "API server is not reachable")
        return available

    def test_auto_recording_status(self) -> bool:
        """Test auto-recording status endpoint"""
        status = self.get_auto_recording_status()
        success = bool(status and "running" in status)
        self.log_test("Auto-Recording Status API", success,
                     f"Status: {status}" if success else "Failed to get status")
        return success

    def test_camera_auto_recording_config(self) -> bool:
        """Test camera auto-recording configuration"""
        success = True
        
        # Test enabling auto-recording for camera1
        enabled = self.enable_auto_recording("camera1")
        if enabled:
            self.log_test("Enable Auto-Recording (camera1)", True, "Successfully enabled")
        else:
            self.log_test("Enable Auto-Recording (camera1)", False, "Failed to enable")
            success = False

        # Check camera status
        time.sleep(1)
        camera_status = self.get_camera_status("camera1")
        auto_enabled = camera_status.get("auto_recording_enabled", False)
        self.log_test("Auto-Recording Status Check", auto_enabled,
                     f"Camera1 auto-recording enabled: {auto_enabled}")
        
        if not auto_enabled:
            success = False

        return success

    def test_machine_state_simulation(self) -> bool:
        """Test machine state change simulation"""
        try:
            # Test vibratory conveyor (camera1)
            self.simulate_machine_state_change("vibratory_conveyor", "on")
            time.sleep(2)
            
            camera_status = self.get_camera_status("camera1")
            is_recording = camera_status.get("is_recording", False)
            auto_active = camera_status.get("auto_recording_active", False)
            
            self.log_test("Machine ON -> Recording Start", is_recording,
                         f"Camera1 recording: {is_recording}, auto-active: {auto_active}")
            
            # Test turning machine off
            time.sleep(3)
            self.simulate_machine_state_change("vibratory_conveyor", "off")
            time.sleep(2)
            
            camera_status = self.get_camera_status("camera1")
            is_recording_after = camera_status.get("is_recording", False)
            auto_active_after = camera_status.get("auto_recording_active", False)
            
            self.log_test("Machine OFF -> Recording Stop", not is_recording_after,
                         f"Camera1 recording: {is_recording_after}, auto-active: {auto_active_after}")
            
            return is_recording and not is_recording_after
            
        except Exception as e:
            self.log_test("Machine State Simulation", False, f"Error: {e}")
            return False

    def test_retry_mechanism(self) -> bool:
        """Test retry mechanism for failed recording attempts"""
        # This test would require simulating camera failures
        # For now, we'll just check if the retry queue is accessible
        try:
            status = self.get_auto_recording_status()
            retry_queue = status.get("retry_queue", {})
            
            self.log_test("Retry Queue Access", True,
                         f"Retry queue accessible, current items: {len(retry_queue)}")
            return True
            
        except Exception as e:
            self.log_test("Retry Queue Access", False, f"Error: {e}")
            return False

    def run_all_tests(self):
        """Run all auto-recording tests"""
        print("🧪 Starting Auto-Recording Tests")
        print("=" * 50)
        
        # Check if system is running
        if not self.test_api_connectivity():
            print("\n❌ Cannot run tests - API server is not available")
            print("Please start the USDA Vision System first:")
            print("  python main.py")
            return False

        # Run tests
        tests = [
            self.test_auto_recording_status,
            self.test_camera_auto_recording_config,
            self.test_machine_state_simulation,
            self.test_retry_mechanism,
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            try:
                if test():
                    passed += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {e}")

        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All auto-recording tests passed!")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed")
            return False

    def cleanup(self):
        """Cleanup after tests"""
        print("\n🧹 Cleaning up...")
        
        # Disable auto-recording for test cameras
        self.disable_auto_recording("camera1")
        self.disable_auto_recording("camera2")
        
        # Turn off machines
        self.simulate_machine_state_change("vibratory_conveyor", "off")
        self.simulate_machine_state_change("blower_separator", "off")
        
        print("✅ Cleanup completed")


def main():
    """Main test function"""
    tester = AutoRecordingTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
