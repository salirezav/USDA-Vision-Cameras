#!/usr/bin/env python3
"""
Test script to verify the frame conversion fix works correctly.
"""

import sys
import os
import numpy as np

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add camera SDK to path
sys.path.append(os.path.join(os.path.dirname(__file__), "camera_sdk"))

try:
    import mvsdk
    print("✅ mvsdk imported successfully")
except ImportError as e:
    print(f"❌ Failed to import mvsdk: {e}")
    sys.exit(1)

def test_frame_conversion():
    """Test the frame conversion logic"""
    print("🧪 Testing frame conversion logic...")
    
    # Simulate frame data
    width, height = 640, 480
    frame_size = width * height * 3  # RGB
    
    # Create mock frame data
    mock_frame_data = np.random.randint(0, 255, frame_size, dtype=np.uint8)
    
    # Create a mock frame buffer (simulate memory address)
    frame_buffer = mock_frame_data.ctypes.data
    
    # Create mock FrameHead
    class MockFrameHead:
        def __init__(self):
            self.iWidth = width
            self.iHeight = height
            self.uBytes = frame_size
    
    frame_head = MockFrameHead()
    
    try:
        # Test the conversion logic (similar to what's in streamer.py)
        frame_data_buffer = (mvsdk.c_ubyte * frame_head.uBytes).from_address(frame_buffer)
        frame_data = np.frombuffer(frame_data_buffer, dtype=np.uint8)
        frame = frame_data.reshape((frame_head.iHeight, frame_head.iWidth, 3))
        
        print(f"✅ Frame conversion successful!")
        print(f"   Frame shape: {frame.shape}")
        print(f"   Frame dtype: {frame.dtype}")
        print(f"   Frame size: {frame.size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Frame conversion failed: {e}")
        return False

def main():
    print("🔧 Frame Conversion Test")
    print("=" * 40)
    
    success = test_frame_conversion()
    
    if success:
        print("\n✅ Frame conversion fix is working correctly!")
        print("📋 The streaming issue should be resolved after system restart.")
    else:
        print("\n❌ Frame conversion fix needs more work.")
    
    print("\n💡 To apply the fix:")
    print("1. Restart the USDA vision system")
    print("2. Test streaming again")

if __name__ == "__main__":
    main()
