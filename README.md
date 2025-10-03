# Raspberry Pi Video Streaming & Image Capture

This project contains video streaming and image capture applications for Raspberry Pi with various client options.

## Files

### Video Streaming
- `capture_stream.py` - Video streaming server for Raspberry Pi
- `stream_client.py` - Simple client to receive and save video
- `realtime_client.py` - Real-time client with threading support

### Image Capture API
- `capture_api_client.py` - Captures images every 500ms and sends to REST API
- `test_api.py` - Test script to verify API endpoint functionality

## Setup

### Server (Raspberry Pi)
1. Make sure you have a Raspberry Pi with camera module
2. Install required packages:
   ```bash
   pip3 install picamera2 requests pillow numpy
   ```

### Video Streaming
3. Run the video streaming server:
   ```bash
   python3 capture_stream.py
   ```

### Image Capture API
3. Run the image capture client:
   ```bash
   python3 capture_api_client.py
   ```

### Client (Any computer)
1. Make sure the client computer is on the same network as the Raspberry Pi
2. Find your Raspberry Pi's IP address (use `hostname -I` on the Pi)

## Usage

### Image Capture API (`capture_api_client.py`)
Captures images every 500ms and sends them to a REST API server:

```bash
# Default usage (sends to 192.168.18.11:3000/api/capture every 500ms)
python3 capture_api_client.py

# Custom API URL
python3 capture_api_client.py http://localhost:3000/api/capture

# Custom interval (1 second between captures)
python3 capture_api_client.py http://192.168.18.11:3000/api/capture 1.0

# Run for limited time (30 seconds)
python3 capture_api_client.py http://192.168.18.11:3000/api/capture 0.5 30
```

### Test API Endpoint (`test_api.py`)
Test if your API server is working properly:

```bash
# Test default endpoint
python3 test_api.py

# Test custom endpoint
python3 test_api.py http://localhost:3000/api/capture
```

### Video Streaming

### Simple Client (`stream_client.py`)
Receives the entire 20-second video stream and saves it to a file:

```bash
# Basic usage (saves with timestamp)
python3 stream_client.py 192.168.1.100

# Specify output filename
python3 stream_client.py 192.168.1.100 my_video.h264
```

### Real-time Client (`realtime_client.py`)
Receives the stream in real-time with better handling:

```bash
# Basic usage
python3 realtime_client.py 192.168.1.100

# Save to specific file
python3 realtime_client.py 192.168.1.100 captured_stream.h264
```

## Playing the Video

The received `.h264` files can be played with:

- **VLC**: `vlc filename.h264`
- **FFplay**: `ffplay filename.h264`
- **MPV**: `mpv filename.h264`

## Network Configuration

- Server listens on port **10001**
- Make sure this port is not blocked by firewall
- Both devices must be on the same network

## Troubleshooting

1. **Connection refused**: Make sure the server is running and IP address is correct
2. **No video**: Check camera permissions and make sure camera module is enabled
3. **Poor quality**: Adjust bitrate in `capture_stream.py` (currently 1Mbps)
4. **Network issues**: Try pinging the Raspberry Pi to verify connectivity

## Customization

### Change Video Settings
Edit `capture_stream.py`:
- Resolution: Modify `{"size": (1280, 720)}`
- Bitrate: Change `H264Encoder(1000000)` value
- Duration: Adjust `time.sleep(20)`

### Change Network Settings
- Port: Change `10001` to desired port
- Interface: Change `"0.0.0.0"` to specific IP if needed

## Requirements

### Server (Raspberry Pi)
- Python 3
- picamera2
- Raspberry Pi camera module

### Client
- Python 3
- Standard Python libraries (socket, threading, queue)

## Systemd Service (Auto-start on boot)

For automatic startup of the Flask camera server, use the included Makefile:

```bash
# Quick system-wide setup (move project + install + start)
make setup

# Or user-level setup (no sudo required)
make setup-user

# Or step by step:
make move-project    # Move to /opt/bads-rpi
make install         # Install systemd service (system-wide)
# OR
make install-user    # Install systemd service (user-level)
make start           # Start the service

# View all commands:
make help
```

**Installation Options:**
- **System-wide**: Starts at boot time (recommended for headless Pi)
- **User-level**: Starts when pi user logs in (no sudo required)

See `SERVICE_README.md` for detailed systemd service documentation.