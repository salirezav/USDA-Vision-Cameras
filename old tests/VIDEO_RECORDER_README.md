# Camera Video Recorder

A Python script for recording videos from GigE cameras using the provided SDK with custom exposure and gain settings.

## Features

- **List all available cameras** - Automatically detects and displays all connected cameras
- **Custom camera settings** - Set exposure time to 1ms and gain to 3.5x (or custom values)
- **Video recording** - Record videos in AVI format with timestamp filenames
- **Live preview** - Test camera functionality with live preview mode
- **Interactive menu** - User-friendly menu system for all operations
- **Automatic cleanup** - Proper resource management and cleanup

## Requirements

- Python 3.x
- OpenCV (`cv2`)
- NumPy
- Camera SDK (mvsdk) - included in `python demo` directory
- GigE camera connected to the system

## Installation

1. Ensure your GigE camera is connected and properly configured
2. Make sure the `python demo` directory with `mvsdk.py` is present
3. Install required Python packages:
   ```bash
   pip install opencv-python numpy
   ```

## Usage

### Basic Usage

Run the script:
```bash
python camera_video_recorder.py
```

The script will:
1. Display a welcome message and feature overview
2. List all available cameras
3. Let you select a camera (if multiple are available)
4. Allow you to set custom exposure and gain values
5. Present an interactive menu with options

### Menu Options

1. **Start Recording** - Begin video recording with timestamp filename
2. **List Camera Info** - Display detailed camera information
3. **Test Camera (Live Preview)** - View live camera feed without recording
4. **Exit** - Clean up and exit the program

### Default Settings

- **Exposure Time**: 1.0ms (1000 microseconds)
- **Gain**: 3.5x
- **Video Format**: AVI with XVID codec
- **Frame Rate**: 30 FPS
- **Output Directory**: `videos/` (created automatically)

### Recording Controls

- **Start Recording**: Select option 1 from the menu
- **Stop Recording**: Press 'q' in the preview window
- **Video Files**: Saved as `videos/camera_recording_YYYYMMDD_HHMMSS.avi`

## File Structure

```
camera_video_recorder.py    # Main script
python demo/
    mvsdk.py               # Camera SDK wrapper
    (other demo files)
videos/                    # Output directory (created automatically)
    camera_recording_*.avi # Recorded video files
```

## Script Features

### CameraVideoRecorder Class

- `list_cameras()` - Enumerate and display available cameras
- `initialize_camera()` - Set up camera with custom exposure and gain
- `start_recording()` - Initialize video writer and begin recording
- `stop_recording()` - Stop recording and save video file
- `record_loop()` - Main recording loop with live preview
- `cleanup()` - Proper resource cleanup

### Key Functions

- **Camera Detection**: Automatically finds all connected GigE cameras
- **Settings Validation**: Checks and clamps exposure/gain values to camera limits
- **Frame Processing**: Handles both monochrome and color cameras
- **Windows Compatibility**: Handles frame flipping for Windows systems
- **Error Handling**: Comprehensive error handling and user feedback

## Example Output

```
Camera Video Recorder
====================
This script allows you to:
- List all available cameras
- Record videos with custom exposure (1ms) and gain (3.5x) settings
- Save videos with timestamps
- Stop recording anytime with 'q' key

Found 1 camera(s):
0: GigE Camera Model (GigE) - SN: 12345678

Using camera: GigE Camera Model

Camera Settings:
Enter exposure time in ms (default 1.0): 1.0
Enter gain value (default 3.5): 3.5

Initializing camera with:
- Exposure: 1.0ms
- Gain: 3.5x

Camera type: Color
Set exposure time: 1000.0μs
Set analog gain: 3.50x (range: 1.00 - 16.00)
Camera started successfully

==================================================
Camera Video Recorder Menu
==================================================
1. Start Recording
2. List Camera Info
3. Test Camera (Live Preview)
4. Exit

Select option (1-4): 1

Started recording to: videos/camera_recording_20241223_143022.avi
Frame size: (1920, 1080), FPS: 30.0
Press 'q' to stop recording...
Recording... Press 'q' in the preview window to stop

Recording stopped!
Saved: videos/camera_recording_20241223_143022.avi
Frames recorded: 450
Duration: 15.2 seconds
Average FPS: 29.6
```

## Troubleshooting

### Common Issues

1. **"No cameras found!"**
   - Check camera connection
   - Verify camera power
   - Ensure network configuration for GigE cameras

2. **"SDK initialization failed"**
   - Verify `python demo/mvsdk.py` exists
   - Check camera drivers are installed

3. **"Camera initialization failed"**
   - Camera may be in use by another application
   - Try disconnecting and reconnecting the camera

4. **Recording issues**
   - Ensure sufficient disk space
   - Check write permissions in the output directory

### Performance Tips

- Close other applications using the camera
- Ensure adequate system resources (CPU, RAM)
- Use SSD storage for better write performance
- Adjust frame rate if experiencing dropped frames

## Customization

You can modify the script to:
- Change video codec (currently XVID)
- Adjust target frame rate
- Modify output filename format
- Add additional camera settings
- Change preview window size

## Notes

- Videos are saved in the `videos/` directory with timestamp filenames
- The script handles both monochrome and color cameras automatically
- Frame flipping is handled automatically for Windows systems
- All resources are properly cleaned up on exit
