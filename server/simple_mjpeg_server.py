#!/usr/bin/python3
"""
Simplified MJPEG streaming server for Raspberry Pi Zero 2 W
This version sends raw MJPEG frames without complex overlay processing
"""

import socket
import time
import gc
import sys
import os
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

# Try to import face detection (optional)
try:
    from face_detection import create_face_detector
    import cv2

    FACE_DETECTION_AVAILABLE = True
except ImportError as e:
    FACE_DETECTION_AVAILABLE = False
    print(f"Face detection not available: {e}")


def optimize_system():
    """Apply system-level optimizations"""
    gc.collect()
    gc.set_threshold(100, 5, 5)
    print("System optimizations applied")


def create_mjpeg_camera():
    """Create camera configured for MJPEG streaming"""
    picam2 = Picamera2()

    # Simple configuration for MJPEG
    config = picam2.create_video_configuration(
        main={"size": (320, 240)},  # Small resolution for Pi Zero
        buffer_count=2,
        queue=False,
    )

    picam2.configure(config)
    return picam2


def get_memory_info():
    """Get available memory in MB"""
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if "MemAvailable:" in line:
                    return int(line.split()[1]) / 1024
    except Exception:
        return 0


def capture_and_process_frame(picam2, face_detector=None):
    """Capture a frame and optionally run face detection on it"""
    if not face_detector:
        return

    try:
        # Capture frame for face detection (separate from video stream)
        frame = picam2.capture_array()

        if len(frame.shape) == 3:
            # Convert RGB to BGR for OpenCV
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            faces = face_detector.detect_faces(bgr_frame)

            if len(faces) > 0:
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] Detected {len(faces)} face(s)")

    except Exception as e:
        print(f"Face detection error: {e}")


def main():
    print("=== Simple MJPEG Stream Server ===")
    print("Resolution: 320x240, MJPEG encoding")

    # Parse command line arguments
    face_detection_enabled = False
    if len(sys.argv) > 1:
        if "--face-detection" in sys.argv or "-f" in sys.argv:
            if FACE_DETECTION_AVAILABLE:
                face_detection_enabled = True
                print("Face detection: ENABLED (background processing)")
            else:
                print("Face detection: REQUESTED but NOT AVAILABLE")
        elif "--help" in sys.argv or "-h" in sys.argv:
            print("Usage: python3 simple_mjpeg_server.py [options]")
            print("Options:")
            print("  -f, --face-detection    Enable background face detection")
            print("  -h, --help             Show this help")
            print("\nThis version streams MJPEG without overlay processing")
            print("Face detection runs in background and logs results")
            return

    if not face_detection_enabled:
        print("Face detection: DISABLED (use -f to enable)")

    # System optimization
    optimize_system()

    # Check initial memory
    initial_mem = get_memory_info()
    print(f"Available memory: {initial_mem:.1f}MB")

    picam2 = create_mjpeg_camera()

    # Use JPEG encoder with moderate quality
    encoder = JpegEncoder(q=70)

    # Initialize face detector if enabled
    face_detector = None
    if face_detection_enabled and FACE_DETECTION_AVAILABLE:
        face_detector = create_face_detector(lightweight=True)
        if not face_detector.is_available():
            print("Face detection initialization failed, disabling...")
            face_detector = None

    # Socket setup
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind(("0.0.0.0", 10001))
        sock.listen(1)

        print("Listening on port 10001...")
        print("Streaming MJPEG - compatible with mjpeg_client.py")

        picam2.start()

        while True:  # Server loop
            try:
                print("Waiting for client...")
                conn, addr = sock.accept()
                print(f"Client connected: {addr}")

                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                stream = conn.makefile("wb", buffering=8192)
                output = FileOutput(stream)

                encoder.output = output
                picam2.start_encoder(encoder)

                print("Streaming MJPEG... (Press Ctrl+C to stop)")

                # Monitoring loop with optional face detection
                check_count = 0
                face_check_count = 0

                while True:
                    time.sleep(2)  # Check every 2 seconds

                    check_count += 1
                    face_check_count += 1

                    # Memory check every 30 seconds
                    if check_count >= 15:
                        mem = get_memory_info()
                        print(f"Memory: {mem:.1f}MB", end="\r")
                        if mem < 40:
                            gc.collect()
                        check_count = 0

                    # Face detection every 4 seconds
                    if face_detector and face_check_count >= 2:
                        capture_and_process_frame(picam2, face_detector)
                        face_check_count = 0

            except BrokenPipeError:
                print("\nClient disconnected")
            except ConnectionResetError:
                print("\nClient connection reset")
            except KeyboardInterrupt:
                print("\nShutting down server...")
                break
            except Exception as e:
                print(f"\nStream error: {e}")
            finally:
                try:
                    picam2.stop_encoder()
                    if "conn" in locals():
                        conn.close()
                    gc.collect()
                except Exception:
                    pass
                print("Client session cleaned up")

    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        try:
            picam2.stop()
            picam2.close()
            sock.close()
        except Exception:
            pass

        final_mem = get_memory_info()
        print(f"Final memory: {final_mem:.1f}MB")
        print("Server shutdown complete")


if __name__ == "__main__":
    main()
