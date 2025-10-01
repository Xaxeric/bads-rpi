# HTTP Camera Server for ESP32

Flask-based HTTP server that streams camera frames from Raspberry Pi to ESP32 devices.

## Features

- **320x240 JPEG streaming** - Optimized for ESP32 memory constraints
- **Single frame endpoint** - Perfect for ESP32 HTTP requests (`/frame`)
- **MJPEG streaming** - For browsers and advanced applications (`/stream`)
- **Face detection** - Optional OpenCV face detection with boxes
- **Memory optimized** - Designed for Raspberry Pi Zero 2 W
- **ESP32 ready** - Includes Arduino client example

## Quick Start

### 1. Install Dependencies

```bash
# Install Flask (if not already installed)
pip install flask

# OpenCV and Picamera2 should already be available
# Face detection uses existing lib/face_detection.py
```

### 2. Start the Server

```bash
# Basic server (no face detection)
python flask_camera_server.py

# With face detection
python flask_camera_server.py --face-detection

# Custom port
python flask_camera_server.py --port=8080
```

### 3. Test the Server

```bash
# Test with Python client
python test_client.py

# Test with different server
python test_client.py 192.168.1.100 5000 5

# Test in browser
# Visit: http://your-pi-ip:5000/stream
```

## API Endpoints

| Endpoint | Description | Best For |
|----------|-------------|----------|
| `GET /` | Server information | Status check |
| `GET /frame` | Single JPEG frame | **ESP32 clients** |
| `GET /stream` | MJPEG stream | Browsers, advanced clients |
| `GET /info` | Server status | Debugging |

## ESP32 Integration

### Hardware Setup
- ESP32 development board
- TFT LCD 240x320 (ST7789 or ILI9341)
- WiFi connection

### Arduino Libraries Required
```
TJpg_Decoder by Bodmer
TFT_eSPI by Bodmer
```

### ESP32 Code
Use the provided `esp32_http_client.ino` file:

1. Update WiFi credentials
2. Set Raspberry Pi IP address
3. Configure TFT_eSPI for your display
4. Upload to ESP32

## Configuration Options

### Server Arguments
```bash
python flask_camera_server.py [options]

Options:
  --face-detection, -f    Enable face detection
  --port=PORT            Server port (default: 5000)
```

### Camera Settings
- **Resolution**: 320x240 (optimized for ESP32)
- **Format**: RGB888 → JPEG
- **Quality**: 85% (balance of quality vs size)
- **Frame rate**: Depends on client requests

### Face Detection
- **Algorithm**: OpenCV Haar cascades
- **Performance**: Lightweight mode for Pi Zero 2 W
- **Detection interval**: 2 seconds (configurable)
- **Visualization**: Green boxes around faces

## Performance

### Raspberry Pi Zero 2 W
- **Memory usage**: ~50-100MB
- **CPU usage**: ~30-50% with face detection
- **Frame rate**: 5-10 FPS depending on client
- **JPEG size**: 8-15KB per frame at 320x240

### ESP32 Client
- **Memory usage**: ~100KB per frame
- **Display rate**: 2 FPS (recommended)
- **Network usage**: ~16-30KB/s
- **Latency**: 200-500ms over WiFi

## Troubleshooting

### Server Issues
```bash
# Check if camera is working
python -c "from picamera2 import Picamera2; print('Camera OK')"

# Test basic Flask
curl http://localhost:5000/

# Check face detection
python flask_camera_server.py -f
```

### ESP32 Issues
- **No image**: Check WiFi connection and server IP
- **Garbled display**: Verify TFT_eSPI configuration
- **Slow updates**: Increase `frameInterval` in ESP32 code
- **Memory errors**: Reduce buffer sizes or frame rate

### Network Issues
- **Timeouts**: Check firewall settings
- **Slow performance**: Use ethernet on Pi if possible
- **High latency**: Reduce JPEG quality or resolution

## File Structure

```
http_server/
├── flask_camera_server.py    # Main Flask server
├── esp32_http_client.ino     # Arduino ESP32 client
├── test_client.py            # Python test client
└── README.md                 # This file
```

## Compared to Other Servers

| Server Type | Protocol | ESP32 Compatibility | Performance |
|-------------|----------|-------------------|-------------|
| **HTTP Server** | HTTP/JPEG | ✅ Excellent | Good |
| MJPEG Server | MJPEG stream | ⚠️ Complex | Good |
| H.264 Server | Raw H.264 | ❌ Difficult | Excellent |
| ESP32 Bitmap | Custom TCP | ✅ Good | Fair |

## Next Steps

1. **Test the server**: Start with basic functionality
2. **Try ESP32 client**: Upload Arduino code to ESP32
3. **Enable face detection**: Add `-f` flag for computer vision
4. **Optimize performance**: Adjust quality/resolution as needed
5. **Add features**: Extend with additional endpoints or processing

## Integration with Existing Code

This HTTP server can work alongside your existing servers:
- **Port 5000**: HTTP/Flask server (this)
- **Port 10001**: ESP32 bitmap server
- **Port 8000**: MJPEG server
- **Port 9999**: H.264 server

Choose the best protocol for your ESP32 application!