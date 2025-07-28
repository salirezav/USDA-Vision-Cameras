# Camera SDK Library

This directory contains the core GigE camera SDK library required for the USDA Vision Camera System.

## Contents

### Core SDK Library
- **`mvsdk.py`** - Python wrapper for the GigE camera SDK
  - Provides Python bindings for camera control functions
  - Handles camera initialization, configuration, and image capture
  - **Critical dependency** - Required for all camera operations

## Important Notes

⚠️ **This is NOT demo code** - This directory contains the core SDK library that the entire system depends on for camera functionality.

### SDK Library Details
- The `mvsdk.py` file is a Python wrapper around the native camera SDK
- It provides ctypes bindings to the underlying C/C++ camera library
- Contains all camera control functions, constants, and data structures
- Used by all camera modules in `usda_vision_system/camera/`

### Dependencies
- Requires the native camera SDK library (`libMVSDK.so` on Linux)
- The native library should be installed system-wide or available in the library path

## Usage

This SDK is automatically imported by the camera modules:
```python
# Imported by camera modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "camera_sdk"))
import mvsdk
```

## Demo Code

For camera usage examples and demo code, see the `../demos/` directory:
- `cv_grab.py` - Basic camera capture example
- `cv_grab2.py` - Multi-camera capture example  
- `cv_grab_callback.py` - Callback-based capture example
- `grab.py` - Simple image capture example

## Troubleshooting

If you encounter camera SDK issues:

1. **Check SDK Installation**:
   ```bash
   ls -la camera_sdk/mvsdk.py
   ```

2. **Test SDK Import**:
   ```bash
   python -c "import sys; sys.path.append('./camera_sdk'); import mvsdk; print('SDK imported successfully')"
   ```

3. **Check Native Library**:
   ```bash
   # On Linux
   ldconfig -p | grep MVSDK
   ```

For more troubleshooting, see the main [README.md](../README.md#troubleshooting).
