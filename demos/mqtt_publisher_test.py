#!/usr/bin/env python3
"""
MQTT Publisher Test Script for USDA Vision Camera System

This script allows you to manually publish test messages to the MQTT topics
to simulate machine state changes for testing purposes.

Usage:
    python mqtt_publisher_test.py

The script provides an interactive menu to:
1. Send 'on' state to vibratory conveyor
2. Send 'off' state to vibratory conveyor  
3. Send 'on' state to blower separator
4. Send 'off' state to blower separator
5. Send custom message
"""

import paho.mqtt.client as mqtt
import time
import sys
from datetime import datetime

# MQTT Configuration (matching your system config)
MQTT_BROKER_HOST = "192.168.1.110"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = None  # Set if your broker requires authentication
MQTT_PASSWORD = None  # Set if your broker requires authentication

# Topics (from your config.json)
MQTT_TOPICS = {
    "vibratory_conveyor": "vision/vibratory_conveyor/state",
    "blower_separator": "vision/blower_separator/state"
}

class MQTTPublisher:
    def __init__(self):
        self.client = None
        self.connected = False
        
    def setup_client(self):
        """Setup MQTT client"""
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            
            if MQTT_USERNAME and MQTT_PASSWORD:
                self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
                
            return True
        except Exception as e:
            print(f"❌ Error setting up MQTT client: {e}")
            return False
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"🔗 Connecting to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
            self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.client.loop_start()  # Start background loop
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.connected
            
        except Exception as e:
            print(f"❌ Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when client connects"""
        if rc == 0:
            self.connected = True
            print(f"✅ Connected to MQTT broker successfully!")
        else:
            self.connected = False
            print(f"❌ Connection failed with return code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when client disconnects"""
        self.connected = False
        print(f"🔌 Disconnected from MQTT broker")
    
    def on_publish(self, client, userdata, mid):
        """Callback when message is published"""
        print(f"📤 Message published successfully (mid: {mid})")
    
    def publish_message(self, topic, payload):
        """Publish a message to a topic"""
        if not self.connected:
            print("❌ Not connected to MQTT broker")
            return False
        
        try:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"📡 [{timestamp}] Publishing message:")
            print(f"   📍 Topic: {topic}")
            print(f"   📄 Payload: '{payload}'")
            
            result = self.client.publish(topic, payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ Message queued for publishing")
                return True
            else:
                print(f"❌ Failed to publish message (error: {result.rc})")
                return False
                
        except Exception as e:
            print(f"❌ Error publishing message: {e}")
            return False
    
    def show_menu(self):
        """Show interactive menu"""
        print("\n" + "=" * 50)
        print("🎛️  MQTT PUBLISHER TEST MENU")
        print("=" * 50)
        print("1. Send 'on' to vibratory conveyor")
        print("2. Send 'off' to vibratory conveyor")
        print("3. Send 'on' to blower separator")
        print("4. Send 'off' to blower separator")
        print("5. Send custom message")
        print("6. Show current topics")
        print("0. Exit")
        print("-" * 50)
    
    def handle_menu_choice(self, choice):
        """Handle menu selection"""
        if choice == "1":
            self.publish_message(MQTT_TOPICS["vibratory_conveyor"], "on")
        elif choice == "2":
            self.publish_message(MQTT_TOPICS["vibratory_conveyor"], "off")
        elif choice == "3":
            self.publish_message(MQTT_TOPICS["blower_separator"], "on")
        elif choice == "4":
            self.publish_message(MQTT_TOPICS["blower_separator"], "off")
        elif choice == "5":
            self.custom_message()
        elif choice == "6":
            self.show_topics()
        elif choice == "0":
            return False
        else:
            print("❌ Invalid choice. Please try again.")
        
        return True
    
    def custom_message(self):
        """Send custom message"""
        print("\n📝 Custom Message")
        print("Available topics:")
        for i, (name, topic) in enumerate(MQTT_TOPICS.items(), 1):
            print(f"  {i}. {name}: {topic}")
        
        try:
            topic_choice = input("Select topic (1-2): ").strip()
            if topic_choice == "1":
                topic = MQTT_TOPICS["vibratory_conveyor"]
            elif topic_choice == "2":
                topic = MQTT_TOPICS["blower_separator"]
            else:
                print("❌ Invalid topic choice")
                return
            
            payload = input("Enter message payload: ").strip()
            if payload:
                self.publish_message(topic, payload)
            else:
                print("❌ Empty payload, message not sent")
                
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
    
    def show_topics(self):
        """Show configured topics"""
        print("\n📋 Configured Topics:")
        for name, topic in MQTT_TOPICS.items():
            print(f"  🏭 {name}: {topic}")
    
    def run(self):
        """Main interactive loop"""
        print("📤 MQTT Publisher Test")
        print("=" * 50)
        print(f"🎯 Broker: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        
        if not self.setup_client():
            return False
        
        if not self.connect():
            print("❌ Failed to connect to MQTT broker")
            return False
        
        try:
            while True:
                self.show_menu()
                choice = input("Enter your choice: ").strip()
                
                if not self.handle_menu_choice(choice):
                    break
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.disconnect()
            print("👋 Goodbye!")
        
        return True

def main():
    """Main function"""
    publisher = MQTTPublisher()
    
    try:
        publisher.run()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
