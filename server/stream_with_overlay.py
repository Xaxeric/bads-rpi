#!/usr/bin/python3
"""
Ultra-lightweight streaming server with face detection overlay for Raspberry Pi Zero 2 W
This version draws face detection boxes on the video stream
"""

import socket
import time
import gc
import sys
import os
import cv2
import numpy as np
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder  # Changed to MJPEG for overlay support
from picamera2.outputs import FileOutput

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

# Try to import face detection (optional)
try:
    from face_detection import create_face_detector

    FACE_DETECTION_AVAILABLE = True
except ImportError as e:
    FACE_DETECTION_AVAILABLE = False
    print(f"Face detection not available: {e}")


class OverlayOutput(FileOutput):
    """Custom output that allows frame processing before encoding"""

    def __init__(self, file, face_detector=None):
        super().__init__(file)
        self.face_detector = face_detector
        self.last_detection_time = 0
        self.detected_faces = []

    def outputframe(self, frame, keyframe=True):
        """Process frame before sending to encoder"""
        try:
            # Convert from YUV420 to RGB if needed
            if len(frame.shape) == 1:  # YUV420 format
                height = int(len(frame) * 2 / 3)
                width = int(height * 4 / 3)
                # Skip YUV conversion for now, too complex for Pi Zero
                return super().outputframe(frame, keyframe)

            # If we have RGB frame, process it
            if len(frame.shape) == 3 and self.face_detector:
                current_time = time.time()

                # Run face detection every 2 seconds
                if current_time - self.last_detection_time > 2.0:
                    # Convert to format face detector expects
                    if frame.shape[2] == 3:  # RGB
                        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    else:
                        bgr_frame = frame

                    # Detect faces
                    faces = self.face_detector.detect_faces(bgr_frame)
                    self.detected_faces = faces
                    self.last_detection_time = current_time

                    if len(faces) > 0:
                        print(f"Overlay: Found {len(faces)} face(s)")

                # Draw faces on frame
                if len(self.detected_faces) > 0:
                    frame = self.draw_faces_on_frame(frame, self.detected_faces)

            return super().outputframe(frame, keyframe)

        except Exception as e:
            print(f"Overlay processing error: {e}")
            return super().outputframe(frame, keyframe)

    def draw_faces_on_frame(self, frame, faces):
        """Draw face rectangles on frame"""
        try:
            for x, y, w, h in faces:
                # Draw green rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Add text
                cv2.putText(
                    frame,
                    "FACE",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                )
            return frame
        except Exception as e:
            print(f"Drawing error: {e}")
            return frame


def optimize_system():
    """Apply system-level optimizations"""
    gc.collect()
    gc.set_threshold(100, 5, 5)
    print("System optimizations applied")


def create_overlay_camera():
    """Create camera configured for overlay processing"""
    picam2 = Picamera2()

    # Use RGB format for easier processing, smaller resolution for Pi Zero
    config = picam2.create_video_configuration(
        main={"size": (320, 240), "format": "RGB888"},  # RGB for easier processing
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


def main():
    print("=== Stream Server with Face Detection Overlay ===")
    print("Resolution: 320x240 RGB, MJPEG encoding with face overlay")

    # Parse command line arguments
    face_detection_enabled = False
    if len(sys.argv) > 1:
        if "--face-detection" in sys.argv or "-f" in sys.argv:
            if FACE_DETECTION_AVAILABLE:
                face_detection_enabled = True
                print("Face detection overlay: ENABLED")
            else:
                print("Face detection: REQUESTED but NOT AVAILABLE")
        elif "--help" in sys.argv or "-h" in sys.argv:
            print("Usage: python3 stream_with_overlay.py [options]")
            print("Options:")
            print("  -f, --face-detection    Enable face detection overlay")
            print("  -h, --help             Show this help")
            print("\nThis version draws face detection boxes on the video stream")
            print("Uses MJPEG encoding (larger bandwidth but supports overlay)")
            return

    if not face_detection_enabled:
        print("Face detection overlay: DISABLED (use -f to enable)")

    # System optimization
    optimize_system()

    # Check initial memory
    initial_mem = get_memory_info()
    print(f"Available memory: {initial_mem:.1f}MB")

    if initial_mem < 120:
        print("WARNING: Low memory for overlay processing!")

    picam2 = create_overlay_camera()

    # Use MJPEG encoder (supports frame processing)
    encoder = JpegEncoder(q=50)  # Quality 50 for smaller files

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
        if face_detection_enabled:
            print("Face boxes will be drawn on video stream")

        picam2.start()

        while True:  # Server loop
            try:
                print("Waiting for client...")
                conn, addr = sock.accept()
                print(f"Client connected: {addr}")

                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                stream = conn.makefile("wb", buffering=8192)

                # Create overlay output
                if face_detector:
                    output = OverlayOutput(stream, face_detector)
                else:
                    output = FileOutput(stream)

                encoder.output = output
                picam2.start_encoder(encoder)

                print("Streaming with overlay... (Press Ctrl+C to stop)")

                # Simple monitoring loop
                check_count = 0
                while True:
                    time.sleep(5)  # Less frequent checks for overlay version

                    check_count += 1
                    if check_count >= 6:  # Every 30 seconds
                        mem = get_memory_info()
                        print(f"Memory: {mem:.1f}MB", end="\r")
                        if mem < 40:
                            gc.collect()
                        check_count = 0

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
