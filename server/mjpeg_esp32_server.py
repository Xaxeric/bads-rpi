#!/usr/bin/python3
"""
MJPEG streaming server optimized for ESP32 with 240x320 TFT LCD
Outputs images at exactly 240x320 resolution for direct ESP32 display
"""

import socket
import time
import gc
import sys
import os
import cv2
import numpy as np
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


class ESP32MJPEGStreamer:
    """MJPEG streamer optimized for ESP32 240x320 display"""

    def __init__(self, face_detector=None, jpeg_quality=60):
        self.face_detector = face_detector
        self.jpeg_quality = jpeg_quality  # Lower quality for ESP32
        self.detected_faces = []
        self.last_detection_time = 0
        self.detection_interval = 2.0  # Slower detection for ESP32

    def process_frame_for_esp32(self, frame):
        """Process and resize frame for ESP32 240x320 display"""
        try:
            # Run face detection on original size for better accuracy
            current_time = time.time()

            if (
                self.face_detector
                and (current_time - self.last_detection_time) > self.detection_interval
            ):
                # Detect faces on original frame
                faces = self.face_detector.detect_faces(frame)

                if len(faces) > 0:
                    # Keep largest face only
                    largest_face = max(faces, key=lambda face: face[2] * face[3])
                    self.detected_faces = [largest_face]
                    print("Face detected for ESP32")
                else:
                    self.detected_faces = []

                self.last_detection_time = current_time

            # Draw face boxes on original size
            if len(self.detected_faces) > 0:
                frame = self.draw_face_boxes(frame)

            # Convert to grayscale first (better performance)
            if len(frame.shape) == 3:
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)

            # Resize to exactly 240x320 for ESP32 (portrait orientation)
            # Original is probably 480x360, we need 240x320
            resized_frame = cv2.resize(frame, (240, 320), interpolation=cv2.INTER_AREA)

            return resized_frame

        except Exception as e:
            print(f"ESP32 frame processing error: {e}")
            # Return a black frame of correct size
            return np.zeros((320, 240, 3), dtype=np.uint8)

    def draw_face_boxes(self, frame):
        """Draw face boxes (will be scaled with frame resize)"""
        try:
            overlay_frame = frame.copy()

            for x, y, w, h in self.detected_faces:
                # White rectangle for visibility
                cv2.rectangle(overlay_frame, (x, y), (x + w, y + h), (255, 255, 255), 2)

                # Add label
                cv2.rectangle(
                    overlay_frame, (x, y - 25), (x + 50, y), (255, 255, 255), -1
                )
                cv2.putText(
                    overlay_frame,
                    "FACE",
                    (x + 2, y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    1,
                )

            return overlay_frame
        except Exception as e:
            print(f"Drawing error: {e}")
            return frame

    def frame_to_jpeg_bytes(self, frame):
        """Convert frame to JPEG bytes optimized for ESP32"""
        try:
            # Lower quality for ESP32 memory constraints
            _, jpeg_buffer = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
            )
            return jpeg_buffer.tobytes()
        except Exception as e:
            print(f"JPEG encoding error: {e}")
            return None


def create_esp32_camera():
    """Create camera optimized for ESP32 requirements"""
    picam2 = Picamera2()

    # Start with a reasonable size that we'll resize to 240x320
    config = picam2.create_still_configuration(
        main={"size": (320, 240), "format": "RGB888"},  # Smaller initial size
        buffer_count=2,
    )

    picam2.configure(config)
    return picam2


def main():
    print("=== MJPEG Server for ESP32 240x320 TFT LCD ===")
    print("Output resolution: 240x320 (portrait)")
    print("Optimized for ESP32 memory and processing constraints")

    # Parse arguments
    face_detection_enabled = False
    if len(sys.argv) > 1:
        if "--face-detection" in sys.argv or "-f" in sys.argv:
            if FACE_DETECTION_AVAILABLE:
                face_detection_enabled = True
                print("Face detection: ENABLED for ESP32")
            else:
                print("Face detection: NOT AVAILABLE")
        elif "--help" in sys.argv or "-h" in sys.argv:
            print("Usage: python3 mjpeg_esp32_server.py [options]")
            print("Options:")
            print("  -f, --face-detection    Enable face detection")
            print("  -h, --help             Show help")
            print("\nOptimized for ESP32 with 240x320 TFT display")
            return

    # Setup
    gc.collect()
    picam2 = create_esp32_camera()

    # Initialize face detector
    face_detector = None
    if face_detection_enabled and FACE_DETECTION_AVAILABLE:
        face_detector = create_face_detector(lightweight=True)

    # Create ESP32-optimized streamer
    streamer = ESP32MJPEGStreamer(
        face_detector, jpeg_quality=50
    )  # Very low quality for ESP32

    # Socket setup
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind(("0.0.0.0", 10001))
        sock.listen(1)
        print("Listening on port 10001 for ESP32 clients...")

        picam2.start()
        time.sleep(1)

        while True:
            try:
                print("Waiting for ESP32 client...")
                conn, addr = sock.accept()
                print(f"ESP32 connected: {addr}")

                frame_count = 0
                start_time = time.time()

                while True:
                    try:
                        # Capture frame
                        frame = picam2.capture_array()

                        # Process for ESP32 (resize to 240x320, face detection, etc.)
                        esp32_frame = streamer.process_frame_for_esp32(frame)

                        # Convert to JPEG
                        jpeg_bytes = streamer.frame_to_jpeg_bytes(esp32_frame)

                        if jpeg_bytes:
                            # Send to ESP32
                            conn.send(jpeg_bytes)
                            frame_count += 1

                            # Show stats
                            if frame_count % 20 == 0:
                                elapsed = time.time() - start_time
                                fps = frame_count / elapsed if elapsed > 0 else 0
                                jpeg_kb = len(jpeg_bytes) / 1024
                                print(
                                    f"Frame {frame_count}, FPS: {fps:.1f}, Size: {jpeg_kb:.1f}KB"
                                )

                        # ESP32-friendly frame rate
                        time.sleep(0.2)  # 5 FPS max for ESP32

                    except (BrokenPipeError, ConnectionResetError):
                        print("ESP32 disconnected")
                        break
                    except Exception as e:
                        print(f"Frame error: {e}")
                        time.sleep(0.5)

            except KeyboardInterrupt:
                print("\nServer stopped")
                break
            except Exception as e:
                print(f"Connection error: {e}")
            finally:
                try:
                    if "conn" in locals():
                        conn.close()
                except Exception:
                    pass

    finally:
        try:
            picam2.stop()
            sock.close()
        except Exception:
            pass
        print("ESP32 server shutdown complete")


if __name__ == "__main__":
    main()
