# MQTT Console Logging & API Guide

## 🎯 Overview

Your USDA Vision Camera System now has **enhanced MQTT console logging** and **comprehensive API endpoints** for monitoring machine status via MQTT.

## ✨ What's New

### 1. **Enhanced Console Logging**
- **Colorful emoji-based console output** for all MQTT events
- **Real-time visibility** of MQTT connections, subscriptions, and messages
- **Clear status indicators** for debugging and monitoring

### 2. **New MQTT Status API Endpoint**
- **GET /mqtt/status** - Detailed MQTT client statistics
- **Message counts, error tracking, uptime monitoring**
- **Real-time connection status and broker information**

### 3. **Existing Machine Status APIs** (already available)
- **GET /machines** - All machine states from MQTT
- **GET /system/status** - Overall system status including MQTT

## 🖥️ Console Logging Examples

When you run the system, you'll see:

```bash
🔗 MQTT CONNECTED: 192.168.1.110:1883
📋 MQTT SUBSCRIBED: vibratory_conveyor → vision/vibratory_conveyor/state
📋 MQTT SUBSCRIBED: blower_separator → vision/blower_separator/state
📡 MQTT MESSAGE: vibratory_conveyor → on
📡 MQTT MESSAGE: blower_separator → off
⚠️ MQTT DISCONNECTED: Unexpected disconnection (code: 1)
🔗 MQTT CONNECTED: 192.168.1.110:1883
```

## 🌐 API Endpoints

### MQTT Status
```http
GET http://localhost:8000/mqtt/status
```

**Response:**
```json
{
  "connected": true,
  "broker_host": "192.168.1.110",
  "broker_port": 1883,
  "subscribed_topics": [
    "vision/vibratory_conveyor/state",
    "vision/blower_separator/state"
  ],
  "last_message_time": "2025-07-28T12:00:00",
  "message_count": 42,
  "error_count": 0,
  "uptime_seconds": 3600.5
}
```

### Machine Status
```http
GET http://localhost:8000/machines
```

**Response:**
```json
{
  "vibratory_conveyor": {
    "name": "vibratory_conveyor",
    "state": "on",
    "last_updated": "2025-07-28T12:00:00",
    "last_message": "on",
    "mqtt_topic": "vision/vibratory_conveyor/state"
  },
  "blower_separator": {
    "name": "blower_separator",
    "state": "off",
    "last_updated": "2025-07-28T12:00:00",
    "last_message": "off",
    "mqtt_topic": "vision/blower_separator/state"
  }
}
```

### System Status
```http
GET http://localhost:8000/system/status
```

**Response:**
```json
{
  "system_started": true,
  "mqtt_connected": true,
  "last_mqtt_message": "2025-07-28T12:00:00",
  "machines": { ... },
  "cameras": { ... },
  "active_recordings": 0,
  "total_recordings": 5,
  "uptime_seconds": 3600.5
}
```

## 🚀 How to Use

### 1. **Start the Full System**
```bash
python main.py
```
You'll see enhanced console logging for all MQTT events.

### 2. **Test MQTT Demo (MQTT only)**
```bash
python demo_mqtt_console.py
```
Shows just the MQTT client with enhanced logging.

### 3. **Test API Endpoints**
```bash
python test_mqtt_logging.py
```
Tests all the API endpoints and shows expected responses.

### 4. **Query APIs Directly**
```bash
# Check MQTT status
curl http://localhost:8000/mqtt/status

# Check machine states
curl http://localhost:8000/machines

# Check overall system status
curl http://localhost:8000/system/status
```

## 🔧 Configuration

The MQTT settings are in `config.json`:

```json
{
  "mqtt": {
    "broker_host": "192.168.1.110",
    "broker_port": 1883,
    "username": null,
    "password": null,
    "topics": {
      "vibratory_conveyor": "vision/vibratory_conveyor/state",
      "blower_separator": "vision/blower_separator/state"
    }
  }
}
```

## 🎨 Console Output Features

- **🔗 Connection Events**: Green for successful connections
- **📋 Subscriptions**: Blue for topic subscriptions
- **📡 Messages**: Real-time message display with machine name and payload
- **⚠️ Warnings**: Yellow for unexpected disconnections
- **❌ Errors**: Red for connection failures and errors
- **❓ Unknown Topics**: Purple for unrecognized MQTT topics

## 📊 Monitoring & Debugging

### Real-time Monitoring
- **Console**: Watch live MQTT events as they happen
- **API**: Query `/mqtt/status` for statistics and health
- **Logs**: Check `usda_vision_system.log` for detailed logs

### Troubleshooting
1. **No MQTT messages?** Check broker connectivity and topic configuration
2. **Connection issues?** Verify broker host/port in config.json
3. **API not responding?** Ensure the system is running with `python main.py`

## 🎯 Use Cases

1. **Development**: See MQTT messages in real-time while developing
2. **Debugging**: Identify connection issues and message patterns
3. **Monitoring**: Use APIs to build dashboards or monitoring tools
4. **Integration**: Query machine states from external applications
5. **Maintenance**: Track MQTT statistics and error rates

---

**🎉 Your MQTT monitoring is now fully enhanced with both console logging and comprehensive APIs!**
