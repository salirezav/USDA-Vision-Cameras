#!/usr/bin/env python3
"""
Test script for the standalone auto-recorder

This script tests the standalone auto-recording functionality by:
1. Starting the auto-recorder
2. Simulating MQTT messages
3. Checking if recordings start/stop correctly
"""

import time
import threading
import paho.mqtt.client as mqtt
from usda_vision_system.recording.standalone_auto_recorder import StandaloneAutoRecorder


def test_mqtt_publisher():
    """Test function that publishes MQTT messages to simulate machine state changes"""
    
    # Wait for auto-recorder to start
    time.sleep(3)
    
    # Create MQTT client for testing
    test_client = mqtt.Client()
    test_client.connect("192.168.1.110", 1883, 60)
    
    print("\n🔄 Testing auto-recording with MQTT messages...")
    
    # Test 1: Turn on vibratory_conveyor (should start camera2 recording)
    print("\n📡 Test 1: Turning ON vibratory_conveyor (should start camera2)")
    test_client.publish("vision/vibratory_conveyor/state", "on")
    time.sleep(3)
    
    # Test 2: Turn on blower_separator (should start camera1 recording)
    print("\n📡 Test 2: Turning ON blower_separator (should start camera1)")
    test_client.publish("vision/blower_separator/state", "on")
    time.sleep(3)
    
    # Test 3: Turn off vibratory_conveyor (should stop camera2 recording)
    print("\n📡 Test 3: Turning OFF vibratory_conveyor (should stop camera2)")
    test_client.publish("vision/vibratory_conveyor/state", "off")
    time.sleep(3)
    
    # Test 4: Turn off blower_separator (should stop camera1 recording)
    print("\n📡 Test 4: Turning OFF blower_separator (should stop camera1)")
    test_client.publish("vision/blower_separator/state", "off")
    time.sleep(3)
    
    print("\n✅ Test completed!")
    
    test_client.disconnect()


def main():
    """Main test function"""
    print("🚀 Starting Standalone Auto-Recorder Test")
    
    # Create auto-recorder
    recorder = StandaloneAutoRecorder()
    
    # Start test publisher in background
    test_thread = threading.Thread(target=test_mqtt_publisher, daemon=True)
    test_thread.start()
    
    # Run auto-recorder for 30 seconds
    try:
        if recorder.start():
            print("✅ Auto-recorder started successfully")
            
            # Run for 30 seconds
            for i in range(30):
                time.sleep(1)
                if i % 5 == 0:
                    print(f"⏱️  Running... {30-i} seconds remaining")
            
        else:
            print("❌ Failed to start auto-recorder")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    finally:
        recorder.stop()
        print("🏁 Test completed")


if __name__ == "__main__":
    main()
