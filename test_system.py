#!/usr/bin/env python3
"""
Test script for the USDA Vision Camera System.

This script performs basic tests to verify system components are working correctly.
"""

import sys
import os
import time
import json
import requests
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from usda_vision_system.core.config import Config
        from usda_vision_system.core.state_manager import StateManager
        from usda_vision_system.core.events import EventSystem
        from usda_vision_system.mqtt.client import MQTTClient
        from usda_vision_system.camera.manager import CameraManager
        from usda_vision_system.storage.manager import StorageManager
        from usda_vision_system.api.server import APIServer
        from usda_vision_system.main import USDAVisionSystem

        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    try:
        from usda_vision_system.core.config import Config

        # Test default config
        config = Config()
        print(f"✅ Default config loaded")
        print(f"   MQTT broker: {config.mqtt.broker_host}:{config.mqtt.broker_port}")
        print(f"   Storage path: {config.storage.base_path}")
        print(f"   Cameras configured: {len(config.cameras)}")

        # Test config file if it exists
        if os.path.exists("config.json"):
            config_file = Config("config.json")
            print(f"✅ Config file loaded")

        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_camera_discovery():
    """Test camera discovery"""
    print("\nTesting camera discovery...")
    try:
        sys.path.append("./python demo")
        import mvsdk

        devices = mvsdk.CameraEnumerateDevice()
        print(f"✅ Camera discovery successful")
        print(f"   Found {len(devices)} camera(s)")

        for i, device in enumerate(devices):
            try:
                name = device.GetFriendlyName()
                port_type = device.GetPortType()
                print(f"   Camera {i}: {name} ({port_type})")
            except Exception as e:
                print(f"   Camera {i}: Error getting info - {e}")

        return True
    except Exception as e:
        print(f"❌ Camera discovery failed: {e}")
        print("   Make sure GigE cameras are connected and python demo library is available")
        return False


def test_storage_setup():
    """Test storage directory setup"""
    print("\nTesting storage setup...")
    try:
        from usda_vision_system.core.config import Config
        from usda_vision_system.storage.manager import StorageManager
        from usda_vision_system.core.state_manager import StateManager

        config = Config()
        state_manager = StateManager()
        storage_manager = StorageManager(config, state_manager)

        # Test storage statistics
        stats = storage_manager.get_storage_statistics()
        print(f"✅ Storage manager initialized")
        print(f"   Base path: {stats.get('base_path', 'Unknown')}")
        print(f"   Total files: {stats.get('total_files', 0)}")

        return True
    except Exception as e:
        print(f"❌ Storage setup failed: {e}")
        return False


def test_mqtt_config():
    """Test MQTT configuration (without connecting)"""
    print("\nTesting MQTT configuration...")
    try:
        from usda_vision_system.core.config import Config
        from usda_vision_system.mqtt.client import MQTTClient
        from usda_vision_system.core.state_manager import StateManager
        from usda_vision_system.core.events import EventSystem

        config = Config()
        state_manager = StateManager()
        event_system = EventSystem()

        mqtt_client = MQTTClient(config, state_manager, event_system)
        status = mqtt_client.get_status()

        print(f"✅ MQTT client initialized")
        print(f"   Broker: {status['broker_host']}:{status['broker_port']}")
        print(f"   Topics: {len(status['subscribed_topics'])}")
        for topic in status["subscribed_topics"]:
            print(f"     - {topic}")

        return True
    except Exception as e:
        print(f"❌ MQTT configuration test failed: {e}")
        return False


def test_system_initialization():
    """Test full system initialization (without starting)"""
    print("\nTesting system initialization...")
    try:
        from usda_vision_system.main import USDAVisionSystem

        # Create system instance
        system = USDAVisionSystem()

        # Check system status
        status = system.get_system_status()
        print(f"✅ System initialized successfully")
        print(f"   Running: {status['running']}")
        print(f"   Components initialized: {len(status['components'])}")

        return True
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False


def test_api_endpoints():
    """Test API endpoints if server is running"""
    print("\nTesting API endpoints...")
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")

            # Test system status endpoint
            try:
                response = requests.get("http://localhost:8000/system/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"   System started: {data.get('system_started', False)}")
                    print(f"   MQTT connected: {data.get('mqtt_connected', False)}")
                    print(f"   Active recordings: {data.get('active_recordings', 0)}")
                else:
                    print(f"⚠️  System status endpoint returned {response.status_code}")
            except Exception as e:
                print(f"⚠️  System status test failed: {e}")

            return True
        else:
            print(f"⚠️  API server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️  API server not running (this is OK if system is not started)")
        return True
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("USDA Vision Camera System - Test Suite")
    print("=" * 50)

    tests = [test_imports, test_configuration, test_camera_discovery, test_storage_setup, test_mqtt_config, test_system_initialization, test_api_endpoints]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! System appears to be working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
