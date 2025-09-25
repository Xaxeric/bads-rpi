#!/usr/bin/python3

import socket
import time
import gc
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput


def create_optimized_camera():
    """Create camera with memory-optimized settings"""
    picam2 = Picamera2()

    # Use smaller resolution and lower buffer count for memory efficiency
    video_config = picam2.create_video_configuration(
        main={"size": (640, 480)},  # Reduced from 1280x720 to save memory
        buffer_count=2,  # Minimum buffer count (default is 4)
        queue=False,  # Disable queue to save memory
    )

    picam2.configure(video_config)
    return picam2


def monitor_memory():
    """Monitor memory usage (optional, for debugging)"""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
            for line in lines:
                if "MemAvailable:" in line:
                    mem_kb = int(line.split()[1])
                    mem_mb = mem_kb / 1024
                    if mem_mb < 50:  # Less than 50MB available
                        print(f"Warning: Low memory! Available: {mem_mb:.1f}MB")
                        gc.collect()  # Force garbage collection
                    break
    except Exception as e:
        print(f"Memory check failed: {e}")


print("Starting optimized video stream server...")
print("Optimizations: Lower resolution (640x480), minimal buffers, garbage collection")

picam2 = create_optimized_camera()

# Use lower bitrate to reduce memory pressure
encoder = H264Encoder(bitrate=500000)  # Reduced from 1000000 to 500000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Set send buffer size
    sock.bind(("0.0.0.0", 10001))
    sock.listen(1)  # Only allow 1 connection

    print("Server listening on port 10001...")
    print("Waiting for client connection...")

    picam2.start()

    try:
        conn, addr = sock.accept()
        print(f"Client connected from {addr}")

        # Configure connection for streaming
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        stream = conn.makefile("wb", buffering=8192)  # Small buffer size
        encoder.output = FileOutput(stream)
        picam2.start_encoder(encoder)

        print("Streaming started. Press Ctrl+C to stop...")

        memory_check_counter = 0

        # Stream forever until keyboard interrupt
        while True:
            time.sleep(1)

            # Check memory every 10 seconds
            memory_check_counter += 1
            if memory_check_counter >= 10:
                monitor_memory()
                memory_check_counter = 0

    except KeyboardInterrupt:
        print("\nStopping stream...")
    except BrokenPipeError:
        print("\nClient disconnected")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        try:
            picam2.stop_encoder()
            picam2.stop()
            picam2.close()
            if "conn" in locals():
                conn.close()
            gc.collect()  # Final cleanup
        except Exception as e:
            print(f"Cleanup error: {e}")
        print("Stream stopped and resources cleaned up.")
