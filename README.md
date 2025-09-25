# Raspberry Pi Video Streaming

This project contains a video streaming server for Raspberry Pi and client applications to receive the stream.

## Files

- `capture_stream.py` - Server running on Raspberry Pi
- `stream_client.py` - Simple client to receive and save video
- `realtime_client.py` - Real-time client with threading support

## Setup

### Server (Raspberry Pi)
1. Make sure you have a Raspberry Pi with camera module
2. Install required packages:
   ```bash
   pip3 install picamera2
   ```
3. Run the server:
   ```bash
   python3 capture_stream.py
   ```

### Client (Any computer)
1. Make sure the client computer is on the same network as the Raspberry Pi
2. Find your Raspberry Pi's IP address (use `hostname -I` on the Pi)

## Usage

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