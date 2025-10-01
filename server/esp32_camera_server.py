#!/usr/bin/python3
"""
ESP32 CameraReceiver compatible server
Implements the protocol that ESP32 CameraReceiver expects
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

try:
    from face_detection import create_face_detector

    FACE_DETECTION_AVAILABLE = True
except ImportError as e:
    FACE_DETECTION_AVAILABLE = False
    print(f"Face detection not available: {e}")


class ESP32CameraServer:
    """Server that implements ESP32 CameraReceiver protocol"""

    def __init__(self, face_detector=None):
        self.face_detector = face_detector
        self.detected_faces = []
        self.last_detection_time = 0
        self.detection_interval = 2.0

    def create_bw_bitmap(self, frame):
        """Convert frame to 1-bit bitmap as ESP32 expects"""
        try:
            print(f"Processing frame: {frame.shape}")

            # Run face detection first
            current_time = time.time()
            if (
                self.face_detector
                and (current_time - self.last_detection_time) > self.detection_interval
            ):
                print("Running face detection...")
                # Convert RGB to BGR for face detection
                if len(frame.shape) == 3:
                    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    faces = self.face_detector.detect_faces(bgr_frame)
                else:
                    faces = self.face_detector.detect_faces(frame)

                if len(faces) > 0:
                    largest_face = max(faces, key=lambda face: face[2] * face[3])
                    self.detected_faces = [largest_face]
                    print(f"Face detected for ESP32: {largest_face}")
                else:
                    self.detected_faces = []
                    print("No faces detected")
                self.last_detection_time = current_time

            # Draw face boxes
            if len(self.detected_faces) > 0:
                print(f"Drawing {len(self.detected_faces)} face boxes")
                for x, y, w, h in self.detected_faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
                    cv2.putText(
                        frame,
                        "FACE",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                    )

            # Convert to grayscale
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            else:
                gray = frame

            # Resize to ESP32 display size (240x320)
            resized = cv2.resize(gray, (240, 320), interpolation=cv2.INTER_AREA)

            # Convert to 1-bit bitmap (threshold)
            _, bw = cv2.threshold(resized, 128, 255, cv2.THRESH_BINARY)

            # Pack into 1-bit format
            bitmap = np.packbits(bw // 255, axis=1)

            bitmap_bytes = bitmap.tobytes()
            print(f"Created bitmap: {len(bitmap_bytes)} bytes for 240x320 display")

            return bitmap_bytes

        except Exception as e:
            print(f"Bitmap creation error: {e}")
            import traceback

            traceback.print_exc()
            # Return empty bitmap of correct size
            return b"\x00" * (240 * 320 // 8)


def create_esp32_camera():
    """Create camera for ESP32 server"""
    picam2 = Picamera2()

    config = picam2.create_still_configuration(
        main={"size": (320, 240), "format": "RGB888"},
        buffer_count=2,
    )

    picam2.configure(config)
    return picam2


def handle_esp32_client(conn, addr, camera_server, picam2):
    """Handle ESP32 CameraReceiver protocol"""
    print(f"ESP32 CameraReceiver connected: {addr}")

    try:
        while True:
            # Read command from ESP32
            try:
                data = conn.recv(1024)
                if not data:
                    break

                # Decode and clean the command
                command = data.decode("utf-8").strip()
                print(f"ESP32 command: '{command}' (raw bytes: {data})")

                if command == "GET_FRAME":
                    try:
                        # Capture frame
                        frame = picam2.capture_array()

                        # Create bitmap
                        bitmap_data = camera_server.create_bw_bitmap(frame)

                        # Send OK response
                        conn.send(b"OK\n")

                        # Send bitmap size (as 4-byte little-endian)
                        size_bytes = len(bitmap_data).to_bytes(4, "little")
                        conn.send(size_bytes)

                        # Send bitmap data
                        conn.send(bitmap_data)

                        print(f"Sent frame: {len(bitmap_data)} bytes")

                    except Exception as e:
                        print(f"Frame capture error: {e}")
                        conn.send(b"ERROR\n")

                elif command:  # Non-empty command
                    print(f"Unknown command: '{command}'")
                    conn.send(b"ERROR\n")
                else:
                    print("Empty command received")

            except UnicodeDecodeError as e:
                print(f"Unicode decode error: {e}")
                conn.send(b"ERROR\n")
            except Exception as e:
                print(f"Command processing error: {e}")
                break

    except Exception as e:
        print(f"Client error: {e}")
    finally:
        conn.close()
        print("ESP32 client disconnected")


def main():
    print("=== ESP32 CameraReceiver Compatible Server ===")
    print("Protocol: GET_FRAME commands with bitmap responses")
    print("Output: 240x320 1-bit bitmap for ESP32 display")

    # Parse arguments
    face_detection_enabled = False
    if len(sys.argv) > 1:
        if "--face-detection" in sys.argv or "-f" in sys.argv:
            if FACE_DETECTION_AVAILABLE:
                face_detection_enabled = True
                print("Face detection: ENABLED")
            else:
                print("Face detection: NOT AVAILABLE")

    # Setup
    gc.collect()
    picam2 = create_esp32_camera()

    # Initialize face detector
    face_detector = None
    if face_detection_enabled and FACE_DETECTION_AVAILABLE:
        face_detector = create_face_detector(lightweight=True)

    camera_server = ESP32CameraServer(face_detector)

    # Socket setup
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind(("0.0.0.0", 10001))
        sock.listen(1)
        print("Listening on port 10001 for ESP32 CameraReceiver...")

        picam2.start()
        time.sleep(1)

        while True:
            try:
                conn, addr = sock.accept()
                handle_esp32_client(conn, addr, camera_server, picam2)

            except KeyboardInterrupt:
                print("\nServer stopped")
                break
            except Exception as e:
                print(f"Connection error: {e}")

    finally:
        try:
            picam2.stop()
            sock.close()
        except Exception:
            pass
        print("ESP32 server shutdown complete")


if __name__ == "__main__":
    main()
