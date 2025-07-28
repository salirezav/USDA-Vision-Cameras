#!/usr/bin/env python3
"""
Test script to demonstrate enhanced MQTT logging and API endpoints.

This script shows:
1. Enhanced console logging for MQTT events
2. New MQTT status API endpoint
3. Machine status API endpoint
"""

import sys
import os
import time
import requests
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_endpoints():
    """Test the API endpoints for MQTT and machine status"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API Endpoints...")
    print("=" * 50)
    
    # Test system status
    try:
        print("\n📊 System Status:")
        response = requests.get(f"{base_url}/system/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   System Started: {data.get('system_started')}")
            print(f"   MQTT Connected: {data.get('mqtt_connected')}")
            print(f"   Last MQTT Message: {data.get('last_mqtt_message')}")
            print(f"   Active Recordings: {data.get('active_recordings')}")
            print(f"   Total Recordings: {data.get('total_recordings')}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
    
    # Test MQTT status
    try:
        print("\n📡 MQTT Status:")
        response = requests.get(f"{base_url}/mqtt/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   Connected: {data.get('connected')}")
            print(f"   Broker: {data.get('broker_host')}:{data.get('broker_port')}")
            print(f"   Message Count: {data.get('message_count')}")
            print(f"   Error Count: {data.get('error_count')}")
            print(f"   Last Message: {data.get('last_message_time')}")
            print(f"   Uptime: {data.get('uptime_seconds'):.1f}s" if data.get('uptime_seconds') else "   Uptime: N/A")
            print(f"   Subscribed Topics:")
            for topic in data.get('subscribed_topics', []):
                print(f"     - {topic}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
    
    # Test machine status
    try:
        print("\n🏭 Machine Status:")
        response = requests.get(f"{base_url}/machines", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                for machine_name, machine_info in data.items():
                    print(f"   {machine_name}:")
                    print(f"     State: {machine_info.get('state')}")
                    print(f"     Last Updated: {machine_info.get('last_updated')}")
                    print(f"     Last Message: {machine_info.get('last_message')}")
                    print(f"     MQTT Topic: {machine_info.get('mqtt_topic')}")
            else:
                print("   No machines found")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")

def main():
    """Main test function"""
    print("🔍 MQTT Logging and API Test")
    print("=" * 50)
    print()
    print("This script tests the enhanced MQTT logging and new API endpoints.")
    print("Make sure the USDA Vision System is running before testing.")
    print()
    
    # Wait a moment
    time.sleep(1)
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print()
    print("📝 What to expect when running the system:")
    print("   🔗 MQTT CONNECTED: [broker_host:port]")
    print("   📋 MQTT SUBSCRIBED: [machine] → [topic]")
    print("   📡 MQTT MESSAGE: [machine] → [payload]")
    print("   ⚠️ MQTT DISCONNECTED: [reason]")
    print()
    print("🌐 API Endpoints available:")
    print("   GET /system/status - Overall system status")
    print("   GET /mqtt/status - MQTT client status and statistics")
    print("   GET /machines - All machine states from MQTT")
    print("   GET /cameras - Camera statuses")
    print()
    print("💡 To see live MQTT logs, run: python main.py")

if __name__ == "__main__":
    main()
