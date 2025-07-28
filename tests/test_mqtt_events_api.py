#!/usr/bin/env python3
"""
Test script for MQTT events API endpoint

This script tests the new MQTT events history functionality by:
1. Starting the system components
2. Simulating MQTT messages
3. Testing the API endpoint to retrieve events
"""

import asyncio
import time
import requests
import json
from datetime import datetime

# Test configuration
API_BASE_URL = "http://localhost:8000"
MQTT_EVENTS_ENDPOINT = f"{API_BASE_URL}/mqtt/events"

def test_api_endpoint():
    """Test the MQTT events API endpoint"""
    print("🧪 Testing MQTT Events API Endpoint")
    print("=" * 50)
    
    try:
        # Test basic endpoint
        print("📡 Testing GET /mqtt/events (default limit=5)")
        response = requests.get(MQTT_EVENTS_ENDPOINT)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response successful")
            print(f"📊 Total events: {data.get('total_events', 0)}")
            print(f"📋 Events returned: {len(data.get('events', []))}")
            
            if data.get('events'):
                print(f"🕐 Last updated: {data.get('last_updated')}")
                print("\n📝 Recent events:")
                for i, event in enumerate(data['events'], 1):
                    timestamp = datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S')
                    print(f"   {i}. [{timestamp}] {event['machine_name']}: {event['payload']} -> {event['normalized_state']}")
            else:
                print("📭 No events found")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: API server not running")
        print("   Start the system first: python -m usda_vision_system.main")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test with custom limit
    try:
        print("📡 Testing GET /mqtt/events?limit=10")
        response = requests.get(f"{MQTT_EVENTS_ENDPOINT}?limit=10")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response successful")
            print(f"📋 Events returned: {len(data.get('events', []))}")
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_system_status():
    """Test system status to verify API is running"""
    print("🔍 Checking System Status")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/system/status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ System Status: {'Running' if data.get('system_started') else 'Not Started'}")
            print(f"🔗 MQTT Connected: {'Yes' if data.get('mqtt_connected') else 'No'}")
            print(f"📡 Last MQTT Message: {data.get('last_mqtt_message', 'None')}")
            print(f"⏱️  Uptime: {data.get('uptime_seconds', 0):.1f} seconds")
            return True
        else:
            print(f"❌ System Status Error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: API server not running")
        print("   Start the system first: python -m usda_vision_system.main")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_mqtt_status():
    """Test MQTT status"""
    print("📡 Checking MQTT Status")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/mqtt/status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔗 MQTT Connected: {'Yes' if data.get('connected') else 'No'}")
            print(f"🏠 Broker: {data.get('broker_host')}:{data.get('broker_port')}")
            print(f"📋 Subscribed Topics: {len(data.get('subscribed_topics', []))}")
            print(f"📊 Message Count: {data.get('message_count', 0)}")
            print(f"❌ Error Count: {data.get('error_count', 0)}")
            
            if data.get('subscribed_topics'):
                print("📍 Topics:")
                for topic in data['subscribed_topics']:
                    print(f"   - {topic}")
            
            return True
        else:
            print(f"❌ MQTT Status Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 MQTT Events API Test")
    print("=" * 60)
    print(f"🎯 API Base URL: {API_BASE_URL}")
    print(f"📡 Events Endpoint: {MQTT_EVENTS_ENDPOINT}")
    print()
    
    # Test system status first
    if not test_system_status():
        print("\n❌ System not running. Please start the system first:")
        print("   python -m usda_vision_system.main")
        return
    
    print()
    
    # Test MQTT status
    if not test_mqtt_status():
        print("\n❌ MQTT not available")
        return
    
    print()
    
    # Test the events API
    test_api_endpoint()
    
    print("\n" + "=" * 60)
    print("🎯 Test Instructions:")
    print("1. Make sure the system is running")
    print("2. Turn machines on/off to generate MQTT events")
    print("3. Run this test again to see the events")
    print("4. Check the admin dashboard to see events displayed")
    print()
    print("📋 API Usage:")
    print(f"   GET {MQTT_EVENTS_ENDPOINT}")
    print(f"   GET {MQTT_EVENTS_ENDPOINT}?limit=10")

if __name__ == "__main__":
    main()
