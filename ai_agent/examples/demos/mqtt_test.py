#!/usr/bin/env python3
"""
MQTT Test Script for USDA Vision Camera System

This script tests MQTT message reception by connecting to the broker
and listening for messages on the configured topics.

Usage:
    python mqtt_test.py

The script will:
1. Connect to the MQTT broker
2. Subscribe to all configured topics
3. Display received messages with timestamps
4. Show connection status and statistics
"""

import paho.mqtt.client as mqtt
import time
import json
import signal
import sys
from datetime import datetime
from typing import Dict, Optional

# MQTT Configuration (matching your system config)
MQTT_BROKER_HOST = "192.168.1.110"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = None  # Set if your broker requires authentication
MQTT_PASSWORD = None  # Set if your broker requires authentication

# Topics to monitor (from your config.json)
MQTT_TOPICS = {
    "vibratory_conveyor": "vision/vibratory_conveyor/state",
    "blower_separator": "vision/blower_separator/state"
}

class MQTTTester:
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.message_count = 0
        self.start_time = None
        self.last_message_time = None
        self.received_messages = []
        
    def setup_client(self):
        """Setup MQTT client with callbacks"""
        try:
            # Create MQTT client
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            
            # Set authentication if provided
            if MQTT_USERNAME and MQTT_PASSWORD:
                self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
                print(f"🔐 Using authentication: {MQTT_USERNAME}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up MQTT client: {e}")
            return False
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"🔗 Connecting to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
            self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MQTT broker: {e}")
            return False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when client connects to broker"""
        if rc == 0:
            self.connected = True
            self.start_time = datetime.now()
            print(f"✅ Successfully connected to MQTT broker!")
            print(f"📅 Connection time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Subscribe to all topics
            print("📋 Subscribing to topics:")
            for machine_name, topic in MQTT_TOPICS.items():
                result, mid = client.subscribe(topic)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    print(f"   ✅ {machine_name}: {topic}")
                else:
                    print(f"   ❌ {machine_name}: {topic} (error: {result})")
            
            print()
            print("🎧 Listening for MQTT messages...")
            print("   (Manually turn machines on/off to trigger messages)")
            print("   (Press Ctrl+C to stop)")
            print("-" * 60)
            
        else:
            self.connected = False
            print(f"❌ Connection failed with return code {rc}")
            print("   Return codes:")
            print("   0: Connection successful")
            print("   1: Connection refused - incorrect protocol version")
            print("   2: Connection refused - invalid client identifier")
            print("   3: Connection refused - server unavailable")
            print("   4: Connection refused - bad username or password")
            print("   5: Connection refused - not authorised")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when client disconnects from broker"""
        self.connected = False
        if rc != 0:
            print(f"🔌 Unexpected disconnection from MQTT broker (code: {rc})")
        else:
            print(f"🔌 Disconnected from MQTT broker")
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback when subscription is confirmed"""
        print(f"📋 Subscription confirmed (mid: {mid}, QoS: {granted_qos})")
    
    def on_message(self, client, userdata, msg):
        """Callback when a message is received"""
        try:
            # Decode message
            topic = msg.topic
            payload = msg.payload.decode("utf-8").strip()
            timestamp = datetime.now()
            
            # Update statistics
            self.message_count += 1
            self.last_message_time = timestamp
            
            # Find machine name
            machine_name = "unknown"
            for name, configured_topic in MQTT_TOPICS.items():
                if topic == configured_topic:
                    machine_name = name
                    break
            
            # Store message
            message_data = {
                "timestamp": timestamp,
                "topic": topic,
                "machine": machine_name,
                "payload": payload,
                "message_number": self.message_count
            }
            self.received_messages.append(message_data)
            
            # Display message
            time_str = timestamp.strftime('%H:%M:%S.%f')[:-3]  # Include milliseconds
            print(f"📡 [{time_str}] Message #{self.message_count}")
            print(f"   🏭 Machine: {machine_name}")
            print(f"   📍 Topic: {topic}")
            print(f"   📄 Payload: '{payload}'")
            print(f"   📊 Total messages: {self.message_count}")
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def show_statistics(self):
        """Show connection and message statistics"""
        print("\n" + "=" * 60)
        print("📊 MQTT TEST STATISTICS")
        print("=" * 60)
        
        if self.start_time:
            runtime = datetime.now() - self.start_time
            print(f"⏱️  Runtime: {runtime}")
        
        print(f"🔗 Connected: {'Yes' if self.connected else 'No'}")
        print(f"📡 Messages received: {self.message_count}")
        
        if self.last_message_time:
            print(f"🕐 Last message: {self.last_message_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.received_messages:
            print(f"\n📋 Message Summary:")
            for msg in self.received_messages[-5:]:  # Show last 5 messages
                time_str = msg["timestamp"].strftime('%H:%M:%S')
                print(f"   [{time_str}] {msg['machine']}: {msg['payload']}")
        
        print("=" * 60)
    
    def run(self):
        """Main test loop"""
        print("🧪 MQTT Message Reception Test")
        print("=" * 60)
        print(f"🎯 Broker: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        print(f"📋 Topics: {list(MQTT_TOPICS.values())}")
        print()
        
        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print(f"\n\n🛑 Received interrupt signal, shutting down...")
            self.show_statistics()
            if self.client and self.connected:
                self.client.disconnect()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Setup and connect
        if not self.setup_client():
            return False
        
        if not self.connect():
            return False
        
        # Start the client loop
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
        
        return True

def main():
    """Main function"""
    tester = MQTTTester()
    
    try:
        success = tester.run()
        if not success:
            print("❌ Test failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
