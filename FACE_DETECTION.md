# Face Detection Integration

## Overview

Added OpenCV face detection to the lightweight streaming server with toggleable functionality to minimize memory impact on Pi Zero 2 W.

## Files Added

### `lib/face_detection.py`
- **FaceDetector class**: Memory-optimized face detection
- **Lightweight processing**: Detects faces every 2 seconds (not every frame)
- **Pi Zero optimization**: Scales down images for faster processing
- **Statistics tracking**: Monitors detection performance

### `server/lightweight_stream_with_faces.py`
- **Enhanced streaming server** with face detection capability
- **Toggleable feature**: Can be enabled/disabled via command line
- **Background processing**: Runs face detection parallel to streaming
- **Memory monitoring**: Tracks memory usage with face detection active

### `install_face_detection.sh`
- **Automated installation** of OpenCV dependencies
- **Downloads Haar cascades** for face detection
- **Tests installation** to verify functionality

## Installation

### Option 1: Automatic Installation
```bash
chmod +x install_face_detection.sh
./install_face_detection.sh
```

### Option 2: Manual Installation
```bash
# Install OpenCV
sudo apt update
sudo apt install python3-opencv

# Install Python packages
pip3 install opencv-python-headless numpy
```

## Usage

### Basic Streaming (No Face Detection)
```bash
python3 server/lightweight_stream.py
```

### Streaming with Face Detection
```bash
# Enable face detection
python3 server/lightweight_stream_with_faces.py --face-detection

# Or short form
python3 server/lightweight_stream_with_faces.py -f
```

### Help
```bash
python3 server/lightweight_stream_with_faces.py --help
```

## Memory Impact

| Mode | Memory Usage | CPU Usage | Features |
|------|-------------|-----------|-----------|
| **Basic streaming** | ~50-80MB | Low | Video only |
| **With face detection** | ~80-120MB | Medium | Video + face detection every 2s |

## Face Detection Features

### Optimizations for Pi Zero 2 W:
- **Reduced detection frequency**: Every 2 seconds instead of every frame
- **Image scaling**: Processes smaller images for speed
- **Conservative settings**: Fewer false positives, faster processing
- **Memory management**: Aggressive garbage collection

### Statistics Tracked:
- Total detections performed
- Number of faces found
- Average processing time
- Memory usage monitoring

### Detection Settings:
- **Resolution**: Processes 320px wide images max
- **Minimum face size**: 20x20 pixels
- **Detection interval**: 2 seconds
- **Frame rate impact**: Minimal (separate thread)

## Configuration Options

Edit `lib/face_detection.py` to adjust:

```python
# Create detector with custom settings
detector = FaceDetector(
    detection_interval=3.0,    # Check every 3 seconds
    min_face_size=(15, 15),    # Smaller minimum face
    scale_factor=1.3,          # Faster but less accurate
    min_neighbors=2            # Less strict matching
)
```

## Testing Face Detection

```bash
# Test the face detection library directly
python3 lib/face_detection.py

# Test with camera (if available)
python3 -c "from lib.face_detection import test_face_detection; test_face_detection()"
```

## Performance Tips

### For better performance:
- **Disable GUI**: `sudo systemctl set-default multi-user.target`
- **Close unnecessary processes**: Kill browser, etc.
- **Add swap file**: For memory safety
- **Monitor temperature**: Ensure no thermal throttling

### Memory monitoring during use:
```bash
# Watch memory in real-time
watch -n 2 'free -h | head -3'

# Check if process is using too much memory
ps aux --sort=-%mem | head -10
```

## Troubleshooting

### "Face detection not available"
1. Install OpenCV: `sudo apt install python3-opencv`
2. Install Python packages: `pip3 install opencv-python-headless`
3. Check cascade file: Ensure Haar cascade is installed

### High memory usage
1. Increase detection interval to 5+ seconds
2. Reduce minimum face size
3. Add more swap memory
4. Close other applications

### Poor detection accuracy
1. Decrease detection interval
2. Increase minimum face size
3. Adjust scale_factor (smaller = more accurate, slower)
4. Increase min_neighbors for stricter matching

## Integration with Streaming

The face detection runs **parallel** to video streaming:
- Video stream continues uninterrupted
- Face detection happens in background every 2 seconds
- Results are logged but don't affect video quality
- Memory usage monitored automatically
- Graceful degradation if memory gets low

This design ensures the streaming remains stable while adding face detection capabilities when needed.