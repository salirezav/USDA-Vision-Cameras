#!/usr/bin/env python3
"""
Demo script to show MQTT console logging in action.

This script demonstrates the enhanced MQTT logging by starting just the MQTT client
and showing the console output.
"""

import sys
import os
import time
import signal
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from usda_vision_system.core.config import Config
from usda_vision_system.core.state_manager import StateManager
from usda_vision_system.core.events import EventSystem
from usda_vision_system.core.logging_config import setup_logging
from usda_vision_system.mqtt.client import MQTTClient

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Stopping MQTT demo...")
    sys.exit(0)

def main():
    """Main demo function"""
    print("🚀 MQTT Console Logging Demo")
    print("=" * 50)
    print()
    print("This demo shows enhanced MQTT console logging.")
    print("You'll see colorful console output for MQTT events:")
    print("   🔗 Connection status")
    print("   📋 Topic subscriptions")
    print("   📡 Incoming messages")
    print("   ⚠️ Disconnections and errors")
    print()
    print("Press Ctrl+C to stop the demo.")
    print("=" * 50)
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Setup logging with INFO level for console visibility
        setup_logging(log_level="INFO", log_file="mqtt_demo.log")
        
        # Load configuration
        config = Config()
        
        # Initialize components
        state_manager = StateManager()
        event_system = EventSystem()
        
        # Create MQTT client
        mqtt_client = MQTTClient(config, state_manager, event_system)
        
        print(f"\n🔧 Configuration:")
        print(f"   Broker: {config.mqtt.broker_host}:{config.mqtt.broker_port}")
        print(f"   Topics: {list(config.mqtt.topics.values())}")
        print()
        
        # Start MQTT client
        print("🚀 Starting MQTT client...")
        if mqtt_client.start():
            print("✅ MQTT client started successfully!")
            print("\n👀 Watching for MQTT messages... (Press Ctrl+C to stop)")
            print("-" * 50)
            
            # Keep running and show periodic status
            start_time = time.time()
            last_status_time = start_time
            
            while True:
                time.sleep(1)
                
                # Show status every 30 seconds
                current_time = time.time()
                if current_time - last_status_time >= 30:
                    status = mqtt_client.get_status()
                    uptime = current_time - start_time
                    print(f"\n📊 Status Update (uptime: {uptime:.0f}s):")
                    print(f"   Connected: {status['connected']}")
                    print(f"   Messages: {status['message_count']}")
                    print(f"   Errors: {status['error_count']}")
                    if status['last_message_time']:
                        print(f"   Last Message: {status['last_message_time']}")
                    print("-" * 50)
                    last_status_time = current_time
                    
        else:
            print("❌ Failed to start MQTT client")
            print("   Check your MQTT broker configuration in config.json")
            print("   Make sure the broker is running and accessible")
            
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Cleanup
        try:
            if 'mqtt_client' in locals():
                mqtt_client.stop()
                print("🔌 MQTT client stopped")
        except:
            pass
        
        print("\n👋 Demo completed!")
        print("\n💡 To run the full system with this enhanced logging:")
        print("   python main.py")

if __name__ == "__main__":
    main()
