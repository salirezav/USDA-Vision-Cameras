#!/usr/bin/env python3
"""
Simple test script for auto-recording functionality.

This script performs basic checks to verify that the auto-recording feature
is properly integrated and configured.
"""

import sys
import os
import json
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_config_structure():
    """Test that config.json has the required auto-recording fields"""
    print("🔍 Testing configuration structure...")

    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        # Check system-level auto-recording setting
        system_config = config.get("system", {})
        if "auto_recording_enabled" not in system_config:
            print("❌ Missing 'auto_recording_enabled' in system config")
            return False

        print(f"✅ System auto-recording enabled: {system_config['auto_recording_enabled']}")

        # Check camera-level auto-recording settings
        cameras = config.get("cameras", [])
        if not cameras:
            print("❌ No cameras found in config")
            return False

        for camera in cameras:
            camera_name = camera.get("name", "unknown")
            required_fields = ["auto_start_recording_enabled", "auto_recording_max_retries", "auto_recording_retry_delay_seconds"]

            missing_fields = [field for field in required_fields if field not in camera]
            if missing_fields:
                print(f"❌ Camera {camera_name} missing fields: {missing_fields}")
                return False

            print(f"✅ Camera {camera_name} auto-recording config:")
            print(f"   - Enabled: {camera['auto_start_recording_enabled']}")
            print(f"   - Max retries: {camera['auto_recording_max_retries']}")
            print(f"   - Retry delay: {camera['auto_recording_retry_delay_seconds']}s")
            print(f"   - Machine topic: {camera.get('machine_topic', 'unknown')}")

        return True

    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False


def test_module_imports():
    """Test that all required modules can be imported"""
    print("\n🔍 Testing module imports...")

    try:
        from usda_vision_system.recording.auto_manager import AutoRecordingManager

        print("✅ AutoRecordingManager imported successfully")

        from usda_vision_system.core.config import Config

        config = Config("config.json")
        print("✅ Config loaded successfully")

        from usda_vision_system.core.state_manager import StateManager

        state_manager = StateManager()
        print("✅ StateManager created successfully")

        from usda_vision_system.core.events import EventSystem

        event_system = EventSystem()
        print("✅ EventSystem created successfully")

        # Test creating AutoRecordingManager (without camera_manager for now)
        auto_manager = AutoRecordingManager(config, state_manager, event_system, None)
        print("✅ AutoRecordingManager created successfully")

        return True

    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_camera_mapping():
    """Test camera to machine topic mapping"""
    print("\n🔍 Testing camera to machine mapping...")

    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        cameras = config.get("cameras", [])
        expected_mappings = {"camera1": "blower_separator", "camera2": "vibratory_conveyor"}  # Blower separator  # Conveyor/cracker cam

        for camera in cameras:
            camera_name = camera.get("name")
            machine_topic = camera.get("machine_topic")

            if camera_name in expected_mappings:
                expected_topic = expected_mappings[camera_name]
                if machine_topic == expected_topic:
                    print(f"✅ {camera_name} correctly mapped to {machine_topic}")
                else:
                    print(f"❌ {camera_name} mapped to {machine_topic}, expected {expected_topic}")
                    return False
            else:
                print(f"⚠️  Unknown camera: {camera_name}")

        return True

    except Exception as e:
        print(f"❌ Error checking mappings: {e}")
        return False


def test_api_models():
    """Test that API models include auto-recording fields"""
    print("\n🔍 Testing API models...")

    try:
        from usda_vision_system.api.models import CameraStatusResponse, CameraConfigResponse, AutoRecordingConfigRequest, AutoRecordingConfigResponse, AutoRecordingStatusResponse

        # Check CameraStatusResponse has auto-recording fields
        camera_response = CameraStatusResponse(name="test", status="available", is_recording=False, last_checked="2024-01-01T00:00:00", auto_recording_enabled=True, auto_recording_active=False, auto_recording_failure_count=0)
        print("✅ CameraStatusResponse includes auto-recording fields")

        # Check CameraConfigResponse has auto-recording fields
        config_response = CameraConfigResponse(
            name="test",
            machine_topic="test_topic",
            storage_path="/test",
            enabled=True,
            auto_start_recording_enabled=True,
            auto_recording_max_retries=3,
            auto_recording_retry_delay_seconds=5,
            exposure_ms=1.0,
            gain=1.0,
            target_fps=30.0,
            sharpness=100,
            contrast=100,
            saturation=100,
            gamma=100,
            noise_filter_enabled=False,
            denoise_3d_enabled=False,
            auto_white_balance=True,
            color_temperature_preset=0,
            wb_red_gain=1.0,
            wb_green_gain=1.0,
            wb_blue_gain=1.0,
            anti_flicker_enabled=False,
            light_frequency=1,
            bit_depth=8,
            hdr_enabled=False,
            hdr_gain_mode=0,
        )
        print("✅ CameraConfigResponse includes auto-recording fields")

        print("✅ All auto-recording API models available")
        return True

    except Exception as e:
        print(f"❌ API model error: {e}")
        return False


def main():
    """Run all basic tests"""
    print("🧪 Auto-Recording Integration Test")
    print("=" * 40)

    tests = [test_config_structure, test_module_imports, test_camera_mapping, test_api_models]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")

    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All integration tests passed!")
        print("\n📝 Next steps:")
        print("1. Start the system: python main.py")
        print("2. Run full tests: python tests/test_auto_recording.py")
        print("3. Test with MQTT messages to trigger auto-recording")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print("Please fix the issues before running the full system")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
