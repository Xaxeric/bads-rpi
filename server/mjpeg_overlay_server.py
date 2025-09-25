#!/usr/bin/python3
"""
MJPEG streaming server with face detection boxes overlay for Raspberry Pi Zero 2 W
This version draws face detection boxes directly on the video frames
"""

import socket
import time
import gc
import sys
import os
import cv2
import numpy as np
from io import BytesIO
from picamera2 import Picamera2

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

# Try to import face detection (optional)
try:
    from face_detection import create_face_detector

    FACE_DETECTION_AVAILABLE = True
except ImportError as e:
    FACE_DETECTION_AVAILABLE = False
    print(f"Face detection not available: {e}")


class MJPEGStreamWithOverlay:
    """MJPEG streamer that adds face detection overlay to frames"""

    def __init__(self, face_detector=None, jpeg_quality=70):
        self.face_detector = face_detector
        self.jpeg_quality = jpeg_quality
        self.detected_faces = []
        self.last_detection_time = 0
        self.detection_interval = 1.0  # Detect faces every 1 second

    def process_frame_with_faces(self, frame):
        """Add face detection boxes to frame"""
        current_time = time.time()

        # Run face detection periodically
        if (
            self.face_detector
            and (current_time - self.last_detection_time) > self.detection_interval
        ):
            try:
                # Convert RGB to BGR for OpenCV face detection
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                    # Detect faces
                    faces = self.face_detector.detect_faces(bgr_frame)
                    self.detected_faces = faces
                    self.last_detection_time = current_time

                    print(f"Face detection result: {len(faces)} faces found")  # Debug
                    if len(faces) > 0:
                        print(f"Face coordinates: {faces}")  # Debug
                        print(f"Overlay: Found {len(faces)} face(s)")

            except Exception as e:
                print(f"Face detection error: {e}")

        # Always show if we have cached faces
        if len(self.detected_faces) > 0:
            print(
                f"Drawing overlay with {len(self.detected_faces)} cached faces"
            )  # Debug
            frame = self.draw_face_boxes(frame)
        else:
            print("No faces to draw")  # Debug

        return frame

    def draw_face_boxes(self, frame):
        """Draw green rectangles around detected faces"""
        try:
            # Make a copy to avoid modifying original
            overlay_frame = frame.copy()

            print(f"Drawing {len(self.detected_faces)} face boxes")  # Debug

            for x, y, w, h in self.detected_faces:
                print(f"Drawing box at: x={x}, y={y}, w={w}, h={h}")  # Debug

                # Draw green rectangle (thicker for visibility)
                cv2.rectangle(overlay_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

                # Draw a second rectangle inside for better visibility
                cv2.rectangle(
                    overlay_frame,
                    (x + 2, y + 2),
                    (x + w - 2, y + h - 2),
                    (0, 255, 0),
                    1,
                )

                # Add "FACE" label with background
                cv2.rectangle(
                    overlay_frame, (x, y - 30), (x + 60, y), (0, 255, 0), -1
                )  # Background
                cv2.putText(
                    overlay_frame,
                    "FACE",
                    (x + 5, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 0),
                    2,
                )  # Black text on green

                # Add face number for multiple faces
                if len(self.detected_faces) > 1:
                    face_num = list(self.detected_faces).index((x, y, w, h)) + 1
                    cv2.putText(
                        overlay_frame,
                        f"#{face_num}",
                        (x + w - 30, y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

            return overlay_frame

        except Exception as e:
            print(f"Drawing error: {e}")
            return frame

    def frame_to_jpeg_bytes(self, frame):
        """Convert frame to JPEG bytes"""
        try:
            # Encode frame as JPEG
            _, jpeg_buffer = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
            )
            return jpeg_buffer.tobytes()
        except Exception as e:
            print(f"JPEG encoding error: {e}")
            return None


def optimize_system():
    """Apply system-level optimizations"""
    gc.collect()
    gc.set_threshold(100, 5, 5)
    print("System optimizations applied")


def create_overlay_camera():
    """Create camera configured for overlay processing"""
    picam2 = Picamera2()

    # Configure for RGB output (easier for OpenCV processing)
    config = picam2.create_still_configuration(
        main={"size": (480, 360), "format": "RGB888"},  # RGB for easier processing
        buffer_count=2,
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
    print("=== MJPEG Server with Face Detection Overlay ===")
    print("Resolution: 480x360 RGB, Face boxes drawn on frames")

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
            print("Usage: python3 mjpeg_overlay_server.py [options]")
            print("Options:")
            print("  -f, --face-detection    Enable face detection overlay")
            print("  -h, --help             Show this help")
            print("\nThis version draws face detection boxes on video frames")
            print("Use mjpeg_client.py to receive the stream")
            return

    if not face_detection_enabled:
        print("Face detection overlay: DISABLED (use -f to enable)")

    # System optimization
    optimize_system()

    # Check initial memory
    initial_mem = get_memory_info()
    print(f"Available memory: {initial_mem:.1f}MB")

    if initial_mem < 150:
        print("WARNING: Low memory for overlay processing!")

    picam2 = create_overlay_camera()

    # Initialize face detector if enabled
    face_detector = None
    if face_detection_enabled and FACE_DETECTION_AVAILABLE:
        face_detector = create_face_detector(lightweight=True)
        if not face_detector.is_available():
            print("Face detection initialization failed, disabling...")
            face_detector = None
            face_detection_enabled = False

    # Create MJPEG streamer with overlay
    streamer = MJPEGStreamWithOverlay(face_detector, jpeg_quality=80)

    # Socket setup
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind(("0.0.0.0", 10001))
        sock.listen(1)

        print("Listening on port 10001...")
        if face_detection_enabled:
            print("Face boxes will be visible on video frames")

        picam2.start()
        time.sleep(1)  # Let camera stabilize

        while True:  # Server loop
            try:
                print("Waiting for client...")
                conn, addr = sock.accept()
                print(f"Client connected: {addr}")

                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                print("Streaming MJPEG with face overlay...")

                frame_count = 0
                start_time = time.time()

                while True:
                    try:
                        # Capture frame
                        frame = picam2.capture_array()

                        # Process frame with face detection overlay
                        if face_detection_enabled:
                            frame = streamer.process_frame_with_faces(frame)

                        # Add a test rectangle to verify drawing works
                        cv2.rectangle(
                            frame, (10, 10), (100, 50), (255, 0, 0), 2
                        )  # Blue test rectangle
                        cv2.putText(
                            frame,
                            "TEST",
                            (15, 35),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 0, 0),
                            2,
                        )

                        # Convert frame to JPEG bytes
                        jpeg_bytes = streamer.frame_to_jpeg_bytes(frame)

                        if jpeg_bytes:
                            # Send JPEG frame
                            conn.send(jpeg_bytes)
                            frame_count += 1

                            # Show progress
                            if frame_count % 30 == 0:  # Every 30 frames
                                elapsed = time.time() - start_time
                                fps = frame_count / elapsed if elapsed > 0 else 0
                                print(
                                    f"Frames: {frame_count}, FPS: {fps:.1f}", end="\r"
                                )

                        # Control frame rate (don't overwhelm Pi Zero)
                        time.sleep(0.1)  # ~10 FPS max

                    except BrokenPipeError:
                        print("\nClient disconnected")
                        break
                    except ConnectionResetError:
                        print("\nClient connection reset")
                        break
                    except Exception as e:
                        print(f"Frame processing error: {e}")
                        time.sleep(0.5)  # Brief pause on error

            except KeyboardInterrupt:
                print("\nShutting down server...")
                break
            except Exception as e:
                print(f"\nConnection error: {e}")
            finally:
                try:
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
