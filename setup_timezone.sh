#!/bin/bash

# Time Synchronization Setup for USDA Vision Camera System
# Location: Atlanta, Georgia (Eastern Time Zone)

echo "🕐 Setting up time synchronization for Atlanta, Georgia..."
echo "=================================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Running as root - can make system changes"
    CAN_SUDO=true
else
    echo "Running as user - will use sudo for system changes"
    CAN_SUDO=false
fi

# Function to run commands with appropriate privileges
run_cmd() {
    if [ "$CAN_SUDO" = true ]; then
        "$@"
    else
        sudo "$@"
    fi
}

# 1. Set timezone to Eastern Time (Atlanta, Georgia)
echo "📍 Setting timezone to America/New_York (Eastern Time)..."
if run_cmd timedatectl set-timezone America/New_York; then
    echo "✅ Timezone set successfully"
else
    echo "❌ Failed to set timezone - trying alternative method..."
    if run_cmd ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime; then
        echo "✅ Timezone set using alternative method"
    else
        echo "❌ Failed to set timezone"
    fi
fi

# 2. Install and configure NTP for time synchronization
echo ""
echo "🔄 Setting up NTP time synchronization..."

# Check if systemd-timesyncd is available (modern systems)
if systemctl is-available systemd-timesyncd >/dev/null 2>&1; then
    echo "Using systemd-timesyncd for time synchronization..."
    
    # Enable and start systemd-timesyncd
    run_cmd systemctl enable systemd-timesyncd
    run_cmd systemctl start systemd-timesyncd
    
    # Configure NTP servers (US-based servers for better accuracy)
    echo "Configuring NTP servers..."
    cat << EOF | run_cmd tee /etc/systemd/timesyncd.conf
[Time]
NTP=time.nist.gov pool.ntp.org time.google.com
FallbackNTP=time.cloudflare.com time.windows.com
RootDistanceMaxSec=5
PollIntervalMinSec=32
PollIntervalMaxSec=2048
EOF
    
    # Restart timesyncd to apply new configuration
    run_cmd systemctl restart systemd-timesyncd
    
    echo "✅ systemd-timesyncd configured and started"
    
elif command -v ntpd >/dev/null 2>&1; then
    echo "Using ntpd for time synchronization..."
    
    # Install ntp if not present
    if ! command -v ntpd >/dev/null 2>&1; then
        echo "Installing ntp package..."
        if command -v apt-get >/dev/null 2>&1; then
            run_cmd apt-get update && run_cmd apt-get install -y ntp
        elif command -v yum >/dev/null 2>&1; then
            run_cmd yum install -y ntp
        elif command -v dnf >/dev/null 2>&1; then
            run_cmd dnf install -y ntp
        fi
    fi
    
    # Configure NTP servers
    cat << EOF | run_cmd tee /etc/ntp.conf
# NTP configuration for Atlanta, Georgia
driftfile /var/lib/ntp/ntp.drift

# US-based NTP servers for better accuracy
server time.nist.gov iburst
server pool.ntp.org iburst
server time.google.com iburst
server time.cloudflare.com iburst

# Fallback servers
server 0.us.pool.ntp.org iburst
server 1.us.pool.ntp.org iburst
server 2.us.pool.ntp.org iburst
server 3.us.pool.ntp.org iburst

# Security settings
restrict default kod notrap nomodify nopeer noquery
restrict -6 default kod notrap nomodify nopeer noquery
restrict 127.0.0.1
restrict -6 ::1

# Local clock as fallback
server 127.127.1.0
fudge 127.127.1.0 stratum 10
EOF
    
    # Enable and start NTP service
    run_cmd systemctl enable ntp
    run_cmd systemctl start ntp
    
    echo "✅ NTP configured and started"
    
else
    echo "⚠️  No NTP service found - installing chrony as alternative..."
    
    # Install chrony
    if command -v apt-get >/dev/null 2>&1; then
        run_cmd apt-get update && run_cmd apt-get install -y chrony
    elif command -v yum >/dev/null 2>&1; then
        run_cmd yum install -y chrony
    elif command -v dnf >/dev/null 2>&1; then
        run_cmd dnf install -y chrony
    fi
    
    # Configure chrony
    cat << EOF | run_cmd tee /etc/chrony/chrony.conf
# Chrony configuration for Atlanta, Georgia
server time.nist.gov iburst
server pool.ntp.org iburst
server time.google.com iburst
server time.cloudflare.com iburst

# US pool servers
pool us.pool.ntp.org iburst

driftfile /var/lib/chrony/drift
makestep 1.0 3
rtcsync
EOF
    
    # Enable and start chrony
    run_cmd systemctl enable chrony
    run_cmd systemctl start chrony
    
    echo "✅ Chrony configured and started"
fi

# 3. Force immediate time synchronization
echo ""
echo "⏰ Forcing immediate time synchronization..."

if systemctl is-active systemd-timesyncd >/dev/null 2>&1; then
    run_cmd systemctl restart systemd-timesyncd
    sleep 2
    run_cmd timedatectl set-ntp true
elif systemctl is-active ntp >/dev/null 2>&1; then
    run_cmd ntpdate -s time.nist.gov
    run_cmd systemctl restart ntp
elif systemctl is-active chrony >/dev/null 2>&1; then
    run_cmd chrony sources -v
    run_cmd chronyc makestep
fi

# 4. Configure hardware clock
echo ""
echo "🔧 Configuring hardware clock..."
if run_cmd hwclock --systohc; then
    echo "✅ Hardware clock synchronized with system clock"
else
    echo "⚠️  Could not sync hardware clock (this may be normal in containers)"
fi

# 5. Display current time information
echo ""
echo "📊 Current Time Information:"
echo "================================"
echo "System time: $(date)"
echo "UTC time: $(date -u)"
echo "Timezone: $(timedatectl show --property=Timezone --value 2>/dev/null || cat /etc/timezone 2>/dev/null || echo 'Unknown')"

# Check if timedatectl is available
if command -v timedatectl >/dev/null 2>&1; then
    echo ""
    echo "Time synchronization status:"
    timedatectl status
fi

# 6. Create a time check script for the vision system
echo ""
echo "📝 Creating time verification script..."
cat << 'EOF' > check_time.py
#!/usr/bin/env python3
"""
Time verification script for USDA Vision Camera System
Checks if system time is properly synchronized
"""

import datetime
import pytz
import requests
import json

def check_system_time():
    """Check system time against multiple sources"""
    print("🕐 USDA Vision Camera System - Time Verification")
    print("=" * 50)
    
    # Get local time
    local_time = datetime.datetime.now()
    utc_time = datetime.datetime.utcnow()
    
    # Get Atlanta timezone
    atlanta_tz = pytz.timezone('America/New_York')
    atlanta_time = datetime.datetime.now(atlanta_tz)
    
    print(f"Local system time: {local_time}")
    print(f"UTC time: {utc_time}")
    print(f"Atlanta time: {atlanta_time}")
    print(f"Timezone: {atlanta_time.tzname()}")
    
    # Check against world time API
    try:
        print("\n🌐 Checking against world time API...")
        response = requests.get("http://worldtimeapi.org/api/timezone/America/New_York", timeout=5)
        if response.status_code == 200:
            data = response.json()
            api_time = datetime.datetime.fromisoformat(data['datetime'].replace('Z', '+00:00'))
            
            # Compare times (allow 5 second difference)
            time_diff = abs((atlanta_time.replace(tzinfo=None) - api_time.replace(tzinfo=None)).total_seconds())
            
            print(f"API time: {api_time}")
            print(f"Time difference: {time_diff:.2f} seconds")
            
            if time_diff < 5:
                print("✅ Time is synchronized (within 5 seconds)")
                return True
            else:
                print("❌ Time is NOT synchronized (difference > 5 seconds)")
                return False
        else:
            print("⚠️  Could not reach time API")
            return None
    except Exception as e:
        print(f"⚠️  Error checking time API: {e}")
        return None

if __name__ == "__main__":
    check_system_time()
EOF

chmod +x check_time.py

echo "✅ Time verification script created: check_time.py"

# 7. Add time sync check to the vision system startup
echo ""
echo "🔗 Integrating time sync with vision system..."

# Update the startup script to include time check
if [ -f "start_system.sh" ]; then
    # Create backup
    cp start_system.sh start_system.sh.backup
    
    # Add time sync check to startup script
    sed -i '/# Run system tests first/i\
# Check time synchronization\
echo "🕐 Checking time synchronization..."\
python check_time.py\
echo ""' start_system.sh
    
    echo "✅ Updated start_system.sh to include time verification"
fi

echo ""
echo "🎉 Time synchronization setup complete!"
echo ""
echo "Summary:"
echo "- Timezone set to America/New_York (Eastern Time)"
echo "- NTP synchronization configured and enabled"
echo "- Time verification script created (check_time.py)"
echo "- Startup script updated to check time sync"
echo ""
echo "To verify time sync manually, run: python check_time.py"
echo "Current time: $(date)"
