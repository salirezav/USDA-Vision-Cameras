# coding=utf-8
"""
Simple GigE Camera Capture Script
Captures 10 images every 200 milliseconds and saves them to the images directory.
"""

import os
import time
import numpy as np
import cv2
import platform
from datetime import datetime
import sys

sys.path.append("./python demo")
import mvsdk


def is_camera_ready_for_capture():
    """
    Check if camera is ready for capture.
    Returns: (ready: bool, message: str, camera_info: object or None)
    """
    try:
        # Initialize SDK
        mvsdk.CameraSdkInit(1)

        # Enumerate cameras
        DevList = mvsdk.CameraEnumerateDevice()
        if len(DevList) < 1:
            return False, "No cameras found", None

        DevInfo = DevList[0]

        # Check if already opened
        try:
            if mvsdk.CameraIsOpened(DevInfo):
                return False, f"Camera '{DevInfo.GetFriendlyName()}' is already opened by another process", DevInfo
        except:
            pass  # Some cameras might not support this check

        # Try to initialize
        try:
            hCamera = mvsdk.CameraInit(DevInfo, -1, -1)

            # Quick capture test
            try:
                # Basic setup
                mvsdk.CameraSetTriggerMode(hCamera, 0)
                mvsdk.CameraPlay(hCamera)

                # Try to get one frame with short timeout
                pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 500)  # 0.5 second timeout
                mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)

                # Success - close and return
                mvsdk.CameraUnInit(hCamera)
                return True, f"Camera '{DevInfo.GetFriendlyName()}' is ready for capture", DevInfo

            except mvsdk.CameraException as e:
                mvsdk.CameraUnInit(hCamera)
                if e.error_code == mvsdk.CAMERA_STATUS_TIME_OUT:
                    return False, "Camera timeout - may be busy or not streaming properly", DevInfo
                else:
                    return False, f"Camera capture test failed: {e.message}", DevInfo

        except mvsdk.CameraException as e:
            if e.error_code == mvsdk.CAMERA_STATUS_DEVICE_IS_OPENED:
                return False, f"Camera '{DevInfo.GetFriendlyName()}' is already in use", DevInfo
            elif e.error_code == mvsdk.CAMERA_STATUS_ACCESS_DENY:
                return False, f"Access denied to camera '{DevInfo.GetFriendlyName()}'", DevInfo
            else:
                return False, f"Camera initialization failed: {e.message}", DevInfo

    except Exception as e:
        return False, f"Camera check failed: {str(e)}", None


def get_camera_ranges(hCamera):
    """
    Get the available ranges for camera settings
    """
    try:
        # Get exposure time range
        exp_min, exp_max, exp_step = mvsdk.CameraGetExposureTimeRange(hCamera)
        print(f"Exposure time range: {exp_min:.1f} - {exp_max:.1f} μs (step: {exp_step:.1f})")

        # Get analog gain range
        gain_min, gain_max, gain_step = mvsdk.CameraGetAnalogGainXRange(hCamera)
        print(f"Analog gain range: {gain_min:.2f} - {gain_max:.2f}x (step: {gain_step:.3f})")

        return (exp_min, exp_max, exp_step), (gain_min, gain_max, gain_step)
    except Exception as e:
        print(f"Could not get camera ranges: {e}")
        return None, None


def capture_images(exposure_time_us=2000, analog_gain=1.0):
    """
    Main function to capture images from GigE camera

    Parameters:
    - exposure_time_us: Exposure time in microseconds (default: 2000 = 2ms)
    - analog_gain: Analog gain multiplier (default: 1.0)
    """
    # Check if camera is ready for capture
    print("Checking camera availability...")
    ready, message, camera_info = is_camera_ready_for_capture()

    if not ready:
        print(f"❌ Camera not ready: {message}")
        print("\nPossible solutions:")
        print("- Close any other camera applications (preview software, etc.)")
        print("- Check camera connection and power")
        print("- Wait a moment and try again")
        return False

    print(f"✅ {message}")

    # Initialize SDK (already done in status check, but ensure it's ready)
    try:
        mvsdk.CameraSdkInit(1)  # Initialize SDK with English language
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
        print(f"{i}: {DevInfo.GetFriendlyName()} {DevInfo.GetPortType()}")

    # Select camera (use first one if only one available)
    camera_index = 0 if nDev == 1 else int(input("Select camera index: "))
    DevInfo = DevList[camera_index]
    print(f"Selected camera: {DevInfo.GetFriendlyName()}")

    # Initialize camera
    hCamera = 0
    try:
        hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        print("Camera initialized successfully")
    except mvsdk.CameraException as e:
        print(f"CameraInit Failed({e.error_code}): {e.message}")
        return False

    try:
        # Get camera capabilities
        cap = mvsdk.CameraGetCapability(hCamera)

        # Check if it's a mono or color camera
        monoCamera = cap.sIspCapacity.bMonoSensor != 0
        print(f"Camera type: {'Monochrome' if monoCamera else 'Color'}")

        # Get camera ranges
        exp_range, gain_range = get_camera_ranges(hCamera)

        # Set output format
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
        else:
            mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

        # Set camera to continuous capture mode
        mvsdk.CameraSetTriggerMode(hCamera, 0)

        # Set manual exposure with improved control
        mvsdk.CameraSetAeState(hCamera, 0)  # Disable auto exposure

        # Clamp exposure time to valid range
        if exp_range:
            exp_min, exp_max, exp_step = exp_range
            exposure_time_us = max(exp_min, min(exp_max, exposure_time_us))

        mvsdk.CameraSetExposureTime(hCamera, exposure_time_us)
        print(f"Set exposure time: {exposure_time_us/1000:.1f}ms")

        # Set analog gain
        if gain_range:
            gain_min, gain_max, gain_step = gain_range
            analog_gain = max(gain_min, min(gain_max, analog_gain))

        try:
            mvsdk.CameraSetAnalogGainX(hCamera, analog_gain)
            print(f"Set analog gain: {analog_gain:.2f}x")
        except Exception as e:
            print(f"Could not set analog gain: {e}")

        # Start camera
        mvsdk.CameraPlay(hCamera)
        print("Camera started")

        # Calculate frame buffer size
        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)

        # Allocate frame buffer
        pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

        # Create images directory if it doesn't exist
        if not os.path.exists("images"):
            os.makedirs("images")

        print("Starting image capture...")
        print("Capturing 10 images with 200ms intervals...")

        # Capture 10 images
        for i in range(10):
            try:
                # Get image from camera (timeout: 2000ms)
                pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 2000)

                # Process the raw image data
                mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)

                # Release the raw data buffer
                mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)

                # Handle Windows image flip (images are upside down on Windows)
                if platform.system() == "Windows":
                    mvsdk.CameraFlipFrameBuffer(pFrameBuffer, FrameHead, 1)

                # Convert to numpy array for OpenCV
                frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
                frame = np.frombuffer(frame_data, dtype=np.uint8)

                # Reshape based on camera type
                if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8:
                    frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth))
                else:
                    frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 3))

                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds
                filename = f"images/image_{i+1:02d}_{timestamp}.jpg"

                # Save image using OpenCV
                success = cv2.imwrite(filename, frame)

                if success:
                    print(f"Image {i+1}/10 saved: {filename} ({FrameHead.iWidth}x{FrameHead.iHeight})")
                else:
                    print(f"Failed to save image {i+1}/10")

                # Wait 200ms before next capture (except for the last image)
                if i < 9:
                    time.sleep(0.2)

            except mvsdk.CameraException as e:
                print(f"Failed to capture image {i+1}/10 ({e.error_code}): {e.message}")
                continue

        print("Image capture completed!")

        # Cleanup
        mvsdk.CameraAlignFree(pFrameBuffer)

    finally:
        # Close camera
        mvsdk.CameraUnInit(hCamera)
        print("Camera closed")

    return True


if __name__ == "__main__":
    print("GigE Camera Image Capture Script")
    print("=" * 40)
    print("Note: If images are overexposed, you can adjust the exposure settings:")
    print("- Lower exposure_time_us for darker images (e.g., 1000-5000)")
    print("- Lower analog_gain for less amplification (e.g., 0.5-2.0)")
    print()

    # for cracker
    # You can adjust these values to fix overexposure:
    success = capture_images(exposure_time_us=6000, analog_gain=16.0)  # 2ms exposure (much lower than default 30ms)  # 1x gain (no amplification)
    # for blower
    success = capture_images(exposure_time_us=1000, analog_gain=3.5)  # 2ms exposure (much lower than default 30ms)  # 1x gain (no amplification)

    if success:
        print("\nCapture completed successfully!")
        print("Images saved in the 'images' directory")
    else:
        print("\nCapture failed!")

    input("Press Enter to exit...")
