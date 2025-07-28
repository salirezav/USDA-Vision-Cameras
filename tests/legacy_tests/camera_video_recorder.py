# coding=utf-8
import cv2
import numpy as np
import platform
import time
import threading
from datetime import datetime
import os
import sys

# Add the python demo directory to path to import mvsdk
sys.path.append("python demo")

import mvsdk


class CameraVideoRecorder:
    def __init__(self):
        self.hCamera = 0
        self.pFrameBuffer = 0
        self.cap = None
        self.monoCamera = False
        self.recording = False
        self.video_writer = None
        self.frame_count = 0
        self.start_time = None

    def list_cameras(self):
        """List all available cameras"""
        try:
            # Initialize SDK
            mvsdk.CameraSdkInit(1)
        except Exception as e:
            print(f"SDK initialization failed: {e}")
            return []

        # Enumerate cameras
        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)

        if nDev < 1:
            print("No cameras found!")
            return []

        print(f"\nFound {nDev} camera(s):")
        cameras = []
        for i, DevInfo in enumerate(DevList):
            camera_info = {"index": i, "name": DevInfo.GetFriendlyName(), "port_type": DevInfo.GetPortType(), "serial": DevInfo.GetSn(), "dev_info": DevInfo}
            cameras.append(camera_info)
            print(f"{i}: {camera_info['name']} ({camera_info['port_type']}) - SN: {camera_info['serial']}")

        return cameras

    def initialize_camera(self, dev_info, exposure_ms=1.0, gain=3.5, target_fps=3.0):
        """Initialize camera with specified settings"""
        self.target_fps = target_fps
        try:
            # Initialize camera
            self.hCamera = mvsdk.CameraInit(dev_info, -1, -1)
            print(f"Camera initialized successfully")

            # Get camera capabilities
            self.cap = mvsdk.CameraGetCapability(self.hCamera)
            self.monoCamera = self.cap.sIspCapacity.bMonoSensor != 0
            print(f"Camera type: {'Monochrome' if self.monoCamera else 'Color'}")

            # Set output format
            if self.monoCamera:
                mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
            else:
                mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

            # Calculate RGB buffer size
            FrameBufferSize = self.cap.sResolutionRange.iWidthMax * self.cap.sResolutionRange.iHeightMax * (1 if self.monoCamera else 3)

            # Allocate RGB buffer
            self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

            # Set camera to continuous capture mode
            mvsdk.CameraSetTriggerMode(self.hCamera, 0)

            # Set manual exposure
            mvsdk.CameraSetAeState(self.hCamera, 0)  # Disable auto exposure
            exposure_time_us = exposure_ms * 1000  # Convert ms to microseconds

            # Get exposure range and clamp value
            try:
                exp_min, exp_max, exp_step = mvsdk.CameraGetExposureTimeRange(self.hCamera)
                exposure_time_us = max(exp_min, min(exp_max, exposure_time_us))
                print(f"Exposure range: {exp_min:.1f} - {exp_max:.1f} μs")
            except Exception as e:
                print(f"Could not get exposure range: {e}")

            mvsdk.CameraSetExposureTime(self.hCamera, exposure_time_us)
            print(f"Set exposure time: {exposure_time_us/1000:.1f}ms")

            # Set analog gain
            try:
                gain_min, gain_max, gain_step = mvsdk.CameraGetAnalogGainXRange(self.hCamera)
                gain = max(gain_min, min(gain_max, gain))
                mvsdk.CameraSetAnalogGainX(self.hCamera, gain)
                print(f"Set analog gain: {gain:.2f}x (range: {gain_min:.2f} - {gain_max:.2f})")
            except Exception as e:
                print(f"Could not set analog gain: {e}")

            # Start camera
            mvsdk.CameraPlay(self.hCamera)
            print("Camera started successfully")

            return True

        except mvsdk.CameraException as e:
            print(f"Camera initialization failed({e.error_code}): {e.message}")
            return False

    def start_recording(self, output_filename=None):
        """Start video recording"""
        if self.recording:
            print("Already recording!")
            return False

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"video_{timestamp}.avi"

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_filename) if os.path.dirname(output_filename) else ".", exist_ok=True)

        # Get first frame to determine video properties
        try:
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 2000)
            mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
            mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)

            # Handle Windows frame flipping
            if platform.system() == "Windows":
                mvsdk.CameraFlipFrameBuffer(self.pFrameBuffer, FrameHead, 1)

            # Convert to numpy array
            frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
            frame = np.frombuffer(frame_data, dtype=np.uint8)

            if self.monoCamera:
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth))
                # Convert mono to BGR for video writer
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            else:
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 3))

        except mvsdk.CameraException as e:
            print(f"Failed to get initial frame: {e.message}")
            return False

        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        fps = getattr(self, "target_fps", 3.0)  # Use configured FPS or default to 3.0
        frame_size = (FrameHead.iWidth, FrameHead.iHeight)

        self.video_writer = cv2.VideoWriter(output_filename, fourcc, fps, frame_size)

        if not self.video_writer.isOpened():
            print(f"Failed to open video writer for {output_filename}")
            return False

        self.recording = True
        self.frame_count = 0
        self.start_time = time.time()
        self.output_filename = output_filename

        print(f"Started recording to: {output_filename}")
        print(f"Frame size: {frame_size}, FPS: {fps}")
        print("Press 'q' to stop recording...")

        return True

    def stop_recording(self):
        """Stop video recording"""
        if not self.recording:
            print("Not currently recording!")
            return False

        self.recording = False

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        duration = time.time() - self.start_time if self.start_time else 0
        avg_fps = self.frame_count / duration if duration > 0 else 0

        print(f"\nRecording stopped!")
        print(f"Saved: {self.output_filename}")
        print(f"Frames recorded: {self.frame_count}")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Average FPS: {avg_fps:.1f}")

        return True

    def record_loop(self):
        """Main recording loop"""
        if not self.recording:
            return

        print("Recording... Press 'q' in the preview window to stop")

        while self.recording:
            try:
                # Get frame from camera
                pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)
                mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
                mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)

                # Handle Windows frame flipping
                if platform.system() == "Windows":
                    mvsdk.CameraFlipFrameBuffer(self.pFrameBuffer, FrameHead, 1)

                # Convert to numpy array
                frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
                frame = np.frombuffer(frame_data, dtype=np.uint8)

                if self.monoCamera:
                    frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth))
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                else:
                    frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 3))
                    frame_bgr = frame

                # Write every frame to video (FPS is controlled by video file playback rate)
                if self.video_writer and self.recording:
                    self.video_writer.write(frame_bgr)
                    self.frame_count += 1

                # Show preview (resized for display)
                display_frame = cv2.resize(frame_bgr, (640, 480), interpolation=cv2.INTER_LINEAR)

                # Add small delay to control capture rate based on target FPS
                target_fps = getattr(self, "target_fps", 3.0)
                time.sleep(1.0 / target_fps)

                # Add recording indicator
                cv2.putText(display_frame, f"REC - Frame: {self.frame_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                cv2.imshow("Camera Recording - Press 'q' to stop", display_frame)

                # Check for quit key
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.stop_recording()
                    break

            except mvsdk.CameraException as e:
                if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
                    print(f"Camera error: {e.message}")
                    break

    def cleanup(self):
        """Clean up resources"""
        if self.recording:
            self.stop_recording()

        if self.video_writer:
            self.video_writer.release()

        if self.hCamera > 0:
            mvsdk.CameraUnInit(self.hCamera)
            self.hCamera = 0

        if self.pFrameBuffer:
            mvsdk.CameraAlignFree(self.pFrameBuffer)
            self.pFrameBuffer = 0

        cv2.destroyAllWindows()


def interactive_menu():
    """Interactive menu for camera operations"""
    recorder = CameraVideoRecorder()

    try:
        # List available cameras
        cameras = recorder.list_cameras()
        if not cameras:
            return

        # Select camera
        if len(cameras) == 1:
            selected_camera = cameras[0]
            print(f"\nUsing camera: {selected_camera['name']}")
        else:
            while True:
                try:
                    choice = int(input(f"\nSelect camera (0-{len(cameras)-1}): "))
                    if 0 <= choice < len(cameras):
                        selected_camera = cameras[choice]
                        break
                    else:
                        print("Invalid selection!")
                except ValueError:
                    print("Please enter a valid number!")

        # Get camera settings from user
        print(f"\nCamera Settings:")
        try:
            exposure = float(input("Enter exposure time in ms (default 1.0): ") or "1.0")
            gain = float(input("Enter gain value (default 3.5): ") or "3.5")
            fps = float(input("Enter target FPS (default 3.0): ") or "3.0")
        except ValueError:
            print("Using default values: exposure=1.0ms, gain=3.5x, fps=3.0")
            exposure, gain, fps = 1.0, 3.5, 3.0

        # Initialize camera with specified settings
        print(f"\nInitializing camera with:")
        print(f"- Exposure: {exposure}ms")
        print(f"- Gain: {gain}x")
        print(f"- Target FPS: {fps}")

        if not recorder.initialize_camera(selected_camera["dev_info"], exposure_ms=exposure, gain=gain, target_fps=fps):
            return

        # Menu loop
        while True:
            print(f"\n{'='*50}")
            print("Camera Video Recorder Menu")
            print(f"{'='*50}")
            print("1. Start Recording")
            print("2. List Camera Info")
            print("3. Test Camera (Live Preview)")
            print("4. Exit")

            try:
                choice = input("\nSelect option (1-4): ").strip()

                if choice == "1":
                    # Start recording
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"videos/camera_recording_{timestamp}.avi"

                    # Create videos directory
                    os.makedirs("videos", exist_ok=True)

                    if recorder.start_recording(output_file):
                        recorder.record_loop()

                elif choice == "2":
                    # Show camera info
                    print(f"\nCamera Information:")
                    print(f"Name: {selected_camera['name']}")
                    print(f"Port Type: {selected_camera['port_type']}")
                    print(f"Serial Number: {selected_camera['serial']}")
                    print(f"Type: {'Monochrome' if recorder.monoCamera else 'Color'}")

                elif choice == "3":
                    # Live preview
                    print("\nLive Preview - Press 'q' to stop")
                    preview_loop(recorder)

                elif choice == "4":
                    print("Exiting...")
                    break

                else:
                    print("Invalid option! Please select 1-4.")

            except KeyboardInterrupt:
                print("\nReturning to menu...")
                continue

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        recorder.cleanup()
        print("Cleanup completed")


def preview_loop(recorder):
    """Live preview without recording"""
    print("Live preview mode - Press 'q' to return to menu")

    while True:
        try:
            # Get frame from camera
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(recorder.hCamera, 200)
            mvsdk.CameraImageProcess(recorder.hCamera, pRawData, recorder.pFrameBuffer, FrameHead)
            mvsdk.CameraReleaseImageBuffer(recorder.hCamera, pRawData)

            # Handle Windows frame flipping
            if platform.system() == "Windows":
                mvsdk.CameraFlipFrameBuffer(recorder.pFrameBuffer, FrameHead, 1)

            # Convert to numpy array
            frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(recorder.pFrameBuffer)
            frame = np.frombuffer(frame_data, dtype=np.uint8)

            if recorder.monoCamera:
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth))
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            else:
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 3))
                frame_bgr = frame

            # Show preview (resized for display)
            display_frame = cv2.resize(frame_bgr, (640, 480), interpolation=cv2.INTER_LINEAR)

            # Add info overlay
            cv2.putText(display_frame, f"PREVIEW - {FrameHead.iWidth}x{FrameHead.iHeight}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, "Press 'q' to return to menu", (10, display_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("Camera Preview", display_frame)

            # Check for quit key
            if cv2.waitKey(1) & 0xFF == ord("q"):
                cv2.destroyWindow("Camera Preview")
                break

        except mvsdk.CameraException as e:
            if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
                print(f"Camera error: {e.message}")
                break


def main():
    print("Camera Video Recorder")
    print("====================")
    print("This script allows you to:")
    print("- List all available cameras")
    print("- Record videos with custom exposure (1ms), gain (3.5x), and FPS (3.0) settings")
    print("- Save videos with timestamps")
    print("- Stop recording anytime with 'q' key")
    print()

    interactive_menu()


if __name__ == "__main__":
    main()
