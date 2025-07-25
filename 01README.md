# GigE Camera Image Capture

This project provides simple Python scripts to connect to a GigE camera and capture images using the provided SDK.

## Files Overview

### Demo Files (provided with camera)
- `python demo/mvsdk.py` - Main SDK wrapper library
- `python demo/grab.py` - Basic image capture example
- `python demo/cv_grab.py` - OpenCV-based continuous capture
- `python demo/cv_grab_callback.py` - Callback-based capture
- `python demo/readme.txt` - Original demo documentation

### Custom Scripts
- `camera_capture.py` - Standalone script to capture 10 images with 200ms intervals
- `test.ipynb` - Jupyter notebook with the same functionality
- `images/` - Directory where captured images are saved

## Features

- **Automatic camera detection** - Finds and connects to available GigE cameras
- **Configurable capture** - Currently set to capture 10 images with 200ms intervals
- **Both mono and color support** - Automatically detects camera type
- **Timestamped filenames** - Images saved with date/time stamps
- **Error handling** - Robust error handling for camera operations
- **Cross-platform** - Works on Windows and Linux (with appropriate image flipping)

## Requirements

- Python 3.x
- OpenCV (`cv2`)
- NumPy
- Matplotlib (for Jupyter notebook display)
- GigE camera SDK (MVSDK) - included in `python demo/` directory

## Usage

### Option 1: Standalone Script

Run the standalone Python script:

```bash
python camera_capture.py
```

This will:
1. Initialize the camera SDK
2. Detect available cameras
3. Connect to the first camera found
4. Configure camera settings (manual exposure, continuous mode)
5. Capture 10 images with 200ms intervals
6. Save images to the `images/` directory
7. Clean up and close the camera

### Option 2: Jupyter Notebook

Open and run the `test.ipynb` notebook:

```bash
jupyter notebook test.ipynb
```

The notebook provides the same functionality but with:
- Step-by-step execution
- Detailed explanations
- Visual display of the last captured image
- Better error reporting

## Camera Configuration

The scripts are configured with the following default settings:

- **Trigger Mode**: Continuous capture (mode 0)
- **Exposure**: Manual, 30ms
- **Output Format**: 
  - Monochrome cameras: MONO8
  - Color cameras: BGR8
- **Image Processing**: Automatic ISP processing from RAW to RGB/MONO

## Output

Images are saved in the `images/` directory with the following naming convention:
```
image_XX_YYYYMMDD_HHMMSS_mmm.jpg
```

Where:
- `XX` = Image number (01-10)
- `YYYYMMDD_HHMMSS_mmm` = Timestamp with milliseconds

Example: `image_01_20250722_140530_123.jpg`

## Troubleshooting

### Common Issues

1. **"No camera was found!"**
   - Check camera connection (Ethernet cable)
   - Verify camera power
   - Check network settings (camera and PC should be on same subnet)
   - Ensure camera drivers are installed

2. **"CameraInit Failed"**
   - Camera might be in use by another application
   - Check camera permissions
   - Try restarting the camera or PC

3. **"Failed to capture image"**
   - Check camera settings
   - Verify sufficient lighting
   - Check exposure settings

4. **Images appear upside down**
   - This is handled automatically on Windows
   - Linux users may need to adjust the flip settings

### Network Configuration

For GigE cameras, ensure:
- Camera and PC are on the same network segment
- PC network adapter supports Jumbo frames (recommended)
- Firewall allows camera communication
- Sufficient network bandwidth

## Customization

You can modify the scripts to:

- **Change capture count**: Modify the range in the capture loop
- **Adjust timing**: Change the `time.sleep(0.2)` value
- **Modify exposure**: Change the exposure time parameter
- **Change output format**: Modify file format and quality settings
- **Add image processing**: Insert processing steps before saving

## SDK Reference

The camera SDK (`mvsdk.py`) provides extensive functionality:

- Camera enumeration and initialization
- Image capture and processing
- Parameter configuration (exposure, gain, etc.)
- Trigger modes and timing
- Image format conversion
- Error handling

Refer to the original SDK documentation for advanced features.
