#!/usr/bin/env python3
"""
Test script to verify auto-recording functionality with simulated MQTT messages.

This script tests that:
1. Auto recording manager properly handles machine state changes
2. Recording starts when machine turns "on"
3. Recording stops when machine turns "off"
4. Camera configuration from config.json is used
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def test_auto_recording_with_mqtt():
    """Test auto recording functionality with simulated MQTT messages"""
    print("🧪 Testing Auto Recording with MQTT Messages")
    print("=" * 50)

    try:
        # Import required modules
        from usda_vision_system.core.config import Config
        from usda_vision_system.core.state_manager import StateManager
        from usda_vision_system.core.events import EventSystem, EventType
        from usda_vision_system.recording.auto_manager import AutoRecordingManager

        print("✅ Modules imported successfully")

        # Create system components
        config = Config("config.json")
        state_manager = StateManager()
        event_system = EventSystem()

        # Create a mock camera manager for testing
        class MockCameraManager:
            def __init__(self):
                self.recording_calls = []
                self.stop_calls = []

            def manual_start_recording(self, camera_name, filename, exposure_ms=None, gain=None, fps=None):
                call_info = {"camera_name": camera_name, "filename": filename, "exposure_ms": exposure_ms, "gain": gain, "fps": fps, "timestamp": datetime.now()}
                self.recording_calls.append(call_info)
                print(f"📹 MOCK: Starting recording for {camera_name}")
                print(f"   - Filename: {filename}")
                print(f"   - Settings: exposure={exposure_ms}ms, gain={gain}, fps={fps}")
                return True

            def manual_stop_recording(self, camera_name):
                call_info = {"camera_name": camera_name, "timestamp": datetime.now()}
                self.stop_calls.append(call_info)
                print(f"⏹️  MOCK: Stopping recording for {camera_name}")
                return True

        mock_camera_manager = MockCameraManager()

        # Create auto recording manager
        auto_manager = AutoRecordingManager(config, state_manager, event_system, mock_camera_manager)

        print("✅ Auto recording manager created")

        # Start the auto recording manager
        if not auto_manager.start():
            print("❌ Failed to start auto recording manager")
            return False

        print("✅ Auto recording manager started")

        # Test 1: Simulate blower_separator turning ON (should trigger camera1)
        print("\n🔄 Test 1: Blower separator turns ON")
        print("📡 Publishing machine state change event...")
        # Use the same event system instance that the auto manager is subscribed to
        event_system.publish(EventType.MACHINE_STATE_CHANGED, "test_script", {"machine_name": "blower_separator", "state": "on", "previous_state": None})
        time.sleep(1.0)  # Give more time for event processing

        print(f"📊 Total recording calls so far: {len(mock_camera_manager.recording_calls)}")
        for call in mock_camera_manager.recording_calls:
            print(f"   - {call['camera_name']}: {call['filename']}")

        # Check if recording was started for camera1
        camera1_calls = [call for call in mock_camera_manager.recording_calls if call["camera_name"] == "camera1"]
        if camera1_calls:
            call = camera1_calls[-1]
            print(f"✅ Camera1 recording started with config:")
            print(f"   - Exposure: {call['exposure_ms']}ms (expected: 0.3ms)")
            print(f"   - Gain: {call['gain']} (expected: 4.0)")
            print(f"   - FPS: {call['fps']} (expected: 0)")

            # Verify settings match config.json
            if call["exposure_ms"] == 0.3 and call["gain"] == 4.0 and call["fps"] == 0:
                print("✅ Camera settings match config.json")
            else:
                print("❌ Camera settings don't match config.json")
                return False
        else:
            print("❌ Camera1 recording was not started")
            return False

        # Test 2: Simulate vibratory_conveyor turning ON (should trigger camera2)
        print("\n🔄 Test 2: Vibratory conveyor turns ON")
        event_system.publish(EventType.MACHINE_STATE_CHANGED, "test_script", {"machine_name": "vibratory_conveyor", "state": "on", "previous_state": None})
        time.sleep(0.5)

        # Check if recording was started for camera2
        camera2_calls = [call for call in mock_camera_manager.recording_calls if call["camera_name"] == "camera2"]
        if camera2_calls:
            call = camera2_calls[-1]
            print(f"✅ Camera2 recording started with config:")
            print(f"   - Exposure: {call['exposure_ms']}ms (expected: 0.2ms)")
            print(f"   - Gain: {call['gain']} (expected: 2.0)")
            print(f"   - FPS: {call['fps']} (expected: 0)")

            # Verify settings match config.json
            if call["exposure_ms"] == 0.2 and call["gain"] == 2.0 and call["fps"] == 0:
                print("✅ Camera settings match config.json")
            else:
                print("❌ Camera settings don't match config.json")
                return False
        else:
            print("❌ Camera2 recording was not started")
            return False

        # Test 3: Simulate machines turning OFF
        print("\n🔄 Test 3: Machines turn OFF")
        event_system.publish(EventType.MACHINE_STATE_CHANGED, "test_script", {"machine_name": "blower_separator", "state": "off", "previous_state": None})
        event_system.publish(EventType.MACHINE_STATE_CHANGED, "test_script", {"machine_name": "vibratory_conveyor", "state": "off", "previous_state": None})
        time.sleep(0.5)

        # Check if recordings were stopped
        camera1_stops = [call for call in mock_camera_manager.stop_calls if call["camera_name"] == "camera1"]
        camera2_stops = [call for call in mock_camera_manager.stop_calls if call["camera_name"] == "camera2"]

        if camera1_stops and camera2_stops:
            print("✅ Both cameras stopped recording when machines turned OFF")
        else:
            print(f"❌ Recording stop failed - Camera1 stops: {len(camera1_stops)}, Camera2 stops: {len(camera2_stops)}")
            return False

        # Stop the auto recording manager
        auto_manager.stop()
        print("✅ Auto recording manager stopped")

        print("\n🎉 All auto recording tests passed!")
        print("\n📊 Summary:")
        print(f"   - Total recording starts: {len(mock_camera_manager.recording_calls)}")
        print(f"   - Total recording stops: {len(mock_camera_manager.stop_calls)}")
        print(f"   - Camera1 starts: {len([c for c in mock_camera_manager.recording_calls if c['camera_name'] == 'camera1'])}")
        print(f"   - Camera2 starts: {len([c for c in mock_camera_manager.recording_calls if c['camera_name'] == 'camera2'])}")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the auto recording test"""
    setup_logging()

    success = test_auto_recording_with_mqtt()

    if success:
        print("\n✅ Auto recording functionality is working correctly!")
        print("\n📝 The system should now properly:")
        print("   1. Start recording when machines turn ON")
        print("   2. Stop recording when machines turn OFF")
        print("   3. Use camera settings from config.json")
        print("   4. Generate appropriate filenames with timestamps")
    else:
        print("\n❌ Auto recording test failed!")
        print("Please check the implementation and try again.")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
