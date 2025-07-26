#coding=utf-8
"""
Test script to help find optimal exposure settings for your GigE camera.
This script captures a single test image with different exposure settings.
"""
import os
import sys
import mvsdk
import numpy as np
import cv2
import platform
from datetime import datetime

# Add the python demo directory to path
sys.path.append('./python demo')

def test_exposure_settings():
    """
    Test different exposure settings to find optimal values
    """
    # Initialize SDK
    try:
        mvsdk.CameraSdkInit(1)
        print("SDK initialized successfully")
    except Exception as e:
        print(f"SDK initialization failed: {e}")
        return False
    
    # Enumerate cameras
    DevList = mvsdk.CameraEnumerateDevice()
    nDev = len(DevList)
    
    if nDev < 1:
        print("No camera was found!")
        return False
    
    print(f"Found {nDev} camera(s):")
    for i, DevInfo in enumerate(DevList):
        print(f"  {i}: {DevInfo.GetFriendlyName()} ({DevInfo.GetPortType()})")
    
    # Use first camera
    DevInfo = DevList[0]
    print(f"\nSelected camera: {DevInfo.GetFriendlyName()}")
    
    # Initialize camera
    try:
        hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        print("Camera initialized successfully")
    except mvsdk.CameraException as e:
        print(f"CameraInit Failed({e.error_code}): {e.message}")
        return False
    
    try:
        # Get camera capabilities
        cap = mvsdk.CameraGetCapability(hCamera)
        monoCamera = (cap.sIspCapacity.bMonoSensor != 0)
        print(f"Camera type: {'Monochrome' if monoCamera else 'Color'}")
        
        # Get camera ranges
        try:
            exp_min, exp_max, exp_step = mvsdk.CameraGetExposureTimeRange(hCamera)
            print(f"Exposure time range: {exp_min:.1f} - {exp_max:.1f} μs")
            
            gain_min, gain_max, gain_step = mvsdk.CameraGetAnalogGainXRange(hCamera)
            print(f"Analog gain range: {gain_min:.2f} - {gain_max:.2f}x")
        except Exception as e:
            print(f"Could not get camera ranges: {e}")
            exp_min, exp_max = 100, 100000
            gain_min, gain_max = 1.0, 4.0
        
        # Set output format
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
        else:
            mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)
        
        # Set camera to continuous capture mode
        mvsdk.CameraSetTriggerMode(hCamera, 0)
        mvsdk.CameraSetAeState(hCamera, 0)  # Disable auto exposure
        
        # Start camera
        mvsdk.CameraPlay(hCamera)
        
        # Allocate frame buffer
        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)
        pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)
        
        # Create test directory
        if not os.path.exists("exposure_tests"):
            os.makedirs("exposure_tests")
        
        print("\nTesting different exposure settings...")
        print("=" * 50)
        
        # Test different exposure times (in microseconds)
        exposure_times = [500, 1000, 2000, 5000, 10000, 20000]  # 0.5ms to 20ms
        analog_gains = [1.0]  # Start with 1x gain
        
        test_count = 0
        for exp_time in exposure_times:
            for gain in analog_gains:
                # Clamp values to valid ranges
                exp_time = max(exp_min, min(exp_max, exp_time))
                gain = max(gain_min, min(gain_max, gain))
                
                print(f"\nTest {test_count + 1}: Exposure={exp_time/1000:.1f}ms, Gain={gain:.1f}x")
                
                # Set camera parameters
                mvsdk.CameraSetExposureTime(hCamera, exp_time)
                try:
                    mvsdk.CameraSetAnalogGainX(hCamera, gain)
                except:
                    pass  # Some cameras might not support this
                
                # Wait a moment for settings to take effect
                import time
                time.sleep(0.1)
                
                # Capture image
                try:
                    pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 2000)
                    mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)
                    mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)
                    
                    # Handle Windows image flip
                    if platform.system() == "Windows":
                        mvsdk.CameraFlipFrameBuffer(pFrameBuffer, FrameHead, 1)
                    
                    # Convert to numpy array
                    frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
                    frame = np.frombuffer(frame_data, dtype=np.uint8)
                    
                    if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8:
                        frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth))
                    else:
                        frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 3))
                    
                    # Calculate image statistics
                    mean_brightness = np.mean(frame)
                    max_brightness = np.max(frame)
                    
                    # Save image
                    filename = f"exposure_tests/test_{test_count+1:02d}_exp{exp_time/1000:.1f}ms_gain{gain:.1f}x.jpg"
                    cv2.imwrite(filename, frame)
                    
                    # Provide feedback
                    status = ""
                    if mean_brightness < 50:
                        status = "TOO DARK"
                    elif mean_brightness > 200:
                        status = "TOO BRIGHT"
                    elif max_brightness >= 255:
                        status = "OVEREXPOSED"
                    else:
                        status = "GOOD"
                    
                    print(f"  → Saved: {filename}")
                    print(f"  → Brightness: mean={mean_brightness:.1f}, max={max_brightness:.1f} [{status}]")
                    
                    test_count += 1
                    
                except mvsdk.CameraException as e:
                    print(f"  → Failed to capture: {e.message}")
        
        print(f"\nCompleted {test_count} test captures!")
        print("Check the 'exposure_tests' directory to see the results.")
        print("\nRecommendations:")
        print("- Look for images marked as 'GOOD' - these have optimal exposure")
        print("- If all images are 'TOO BRIGHT', try lower exposure times or gains")
        print("- If all images are 'TOO DARK', try higher exposure times or gains")
        print("- Avoid 'OVEREXPOSED' images as they have clipped highlights")
        
        # Cleanup
        mvsdk.CameraAlignFree(pFrameBuffer)
        
    finally:
        # Close camera
        mvsdk.CameraUnInit(hCamera)
        print("\nCamera closed")
    
    return True

if __name__ == "__main__":
    print("GigE Camera Exposure Test Script")
    print("=" * 40)
    print("This script will test different exposure settings and save sample images.")
    print("Use this to find the optimal settings for your lighting conditions.")
    print()
    
    success = test_exposure_settings()
    
    if success:
        print("\nTesting completed successfully!")
    else:
        print("\nTesting failed!")
    
    input("Press Enter to exit...")
