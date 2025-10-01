# Client-Server Protocol Compatibility

## The Problem

You were trying to use `realtime_client.py` (H.264 client) with `stream_with_overlay.py` (MJPEG server). This creates a **protocol mismatch**:

### **Server Types & Protocols:**

| Server | Encoder | Format | Client Needed |
|--------|---------|--------|---------------|
| `lightweight_stream.py` | H264Encoder | H.264 | `realtime_client.py` |
| `lightweight_stream_with_faces.py` | H264Encoder | H.264 | `realtime_client.py` |
| `stream_with_overlay.py` | JpegEncoder | MJPEG | `mjpeg_client.py` |

### **Why realtime_client.py Didn't Work:**

1. **Server sends**: JPEG frames (binary JPEG data)
2. **Client expects**: H.264 NAL units with start codes (`0x00000001`)
3. **Result**: Client never finds expected frame boundaries, so no frames are processed

## **Solutions:**

### **Option 1: Use Correct Client-Server Pair**

#### **For H.264 Streaming (Recommended for Pi Zero):**
```bash
# Server (Pi Zero)
python3 server/lightweight_stream_with_faces.py -f

# Client (Any computer)  
python3 client/realtime_client.py 192.168.18.66
```

#### **For MJPEG with Face Overlay:**
```bash
# Server (Pi Zero - may be unstable)
python3 server/stream_with_overlay.py -f

# Client (Any computer)
python3 client/mjpeg_client.py 192.168.18.66
```

### **Option 2: Create Universal Client**

A client that auto-detects the stream format, but this adds complexity.

## **Usage Examples:**

### **MJPEG Client Options:**
```bash
# Save as MJPEG file
python3 client/mjpeg_client.py 192.168.18.66 save video.mjpeg

# Save first 10 frames as individual JPEGs  
python3 client/mjpeg_client.py 192.168.18.66 images

# Just count received frames
python3 client/mjpeg_client.py 192.168.18.66 count
```

### **Protocol Detection:**
```bash
# Test what format the server is sending
curl -v http://192.168.18.66:10001 | head -c 100 | hexdump -C

# Look for:
# H.264: 00 00 00 01 (NAL unit start)
# JPEG:  ff d8 ff e0 (JPEG header)
```

## **Recommendation:**

For Pi Zero 2 W, stick with **H.264 streaming**:
- **More stable**: Less memory usage
- **Better compression**: Smaller file sizes  
- **No overlay processing**: Reduced CPU load
- **Face detection still works**: Via console logging

Use the MJPEG overlay version only for testing or when you specifically need to see face detection boxes in the video stream.

## **Quick Fix:**

Since you want to see the face detection working, use the MJPEG client:

```bash
python3 client/mjpeg_client.py 192.168.18.66
```

This should immediately start receiving and saving frames from your overlay server!