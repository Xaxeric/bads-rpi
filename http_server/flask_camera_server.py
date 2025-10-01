#!/usr/bin/python3
"""
Flask HTTP Camera Server for ESP32
Optimized for ESP32 with 320x240 JPEG streaming
"""

import os
import sys
import time
import cv2
from flask import Flask, Response, jsonify
from picamera2 import Picamera2
import threading
import gc

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

try:
    from face_detection import create_face_detector

    FACE_DETECTION_AVAILABLE = True
except ImportError as e:
    FACE_DETECTION_AVAILABLE = False
    print(f"Face detection not available: {e}")

app = Flask(__name__)


class CameraServer:
    def __init__(self):
        self.picam2 = None
        self.face_detector = None
        self.detected_faces = []
        self.last_detection_time = 0
        self.detection_interval = 2.0
        self.face_detection_enabled = False
        self.lock = threading.Lock()

    def initialize_camera(self):
        """Initialize Picamera2 with ESP32-optimized settings"""
        self.picam2 = Picamera2()

        # Configure for 320x240 to match ESP32 requirements
        config = self.picam2.create_still_configuration(
            main={"size": (320, 240), "format": "RGB888"},
            buffer_count=2,
        )

        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(1)  # Allow camera to warm up
        print("Camera initialized at 320x240")

    def enable_face_detection(self):
        """Enable face detection if available"""
        if FACE_DETECTION_AVAILABLE:
            self.face_detector = create_face_detector(lightweight=True)
            self.face_detection_enabled = True
            print("Face detection enabled")
        else:
            print("Face detection not available")

    def process_frame_with_faces(self, frame):
        """Add face detection to frame"""
        current_time = time.time()

        # Run face detection periodically
        if (
            self.face_detector
            and (current_time - self.last_detection_time) > self.detection_interval
        ):
            # Convert RGB to BGR for OpenCV
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            faces = self.face_detector.detect_faces(bgr_frame)

            if len(faces) > 0:
                # Keep only the largest face for better performance
                largest_face = max(faces, key=lambda face: face[2] * face[3])
                self.detected_faces = [largest_face]
                print(f"Face detected: {largest_face}")
            else:
                self.detected_faces = []

            self.last_detection_time = current_time

        # Draw face boxes
        if len(self.detected_faces) > 0:
            for x, y, w, h in self.detected_faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
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

    def capture_jpeg(self):
        """Capture a single JPEG frame"""
        try:
            with self.lock:
                # Capture frame
                frame = self.picam2.capture_array()

                # Add face detection if enabled
                if self.face_detection_enabled:
                    frame = self.process_frame_with_faces(frame)

                # Convert RGB to BGR for JPEG encoding
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Encode to JPEG with optimization for ESP32
                encode_param = [
                    cv2.IMWRITE_JPEG_QUALITY,
                    85,
                ]  # Good quality vs size balance
                success, jpeg_buffer = cv2.imencode(".jpg", bgr_frame, encode_param)

                if success:
                    return jpeg_buffer.tobytes()
                else:
                    print("JPEG encoding failed")
                    return None

        except Exception as e:
            print(f"Capture error: {e}")
            return None

    def cleanup(self):
        """Clean up camera resources"""
        if self.picam2:
            try:
                self.picam2.stop()
            except Exception:
                pass


# Global camera server instance
camera_server = CameraServer()


@app.route("/")
def index():
    """Basic info page"""
    return jsonify(
        {
            "server": "Flask Camera Server for ESP32",
            "resolution": "320x240",
            "endpoints": {
                "single_frame": "/frame",
                "mjpeg_stream": "/stream",
                "server_info": "/info",
            },
            "face_detection": camera_server.face_detection_enabled,
        }
    )


@app.route("/frame")
def get_frame():
    """Get a single JPEG frame - perfect for ESP32"""
    jpeg_data = camera_server.capture_jpeg()

    if jpeg_data:
        return Response(
            jpeg_data,
            mimetype="image/jpeg",
            headers={
                "Content-Length": str(len(jpeg_data)),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    else:
        return "Error capturing frame", 500


@app.route("/stream")
def mjpeg_stream():
    """MJPEG stream - for browsers or advanced ESP32 implementations"""

    def generate():
        while True:
            try:
                jpeg_data = camera_server.capture_jpeg()
                if jpeg_data:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: "
                        + str(len(jpeg_data)).encode()
                        + b"\r\n\r\n"
                        + jpeg_data
                        + b"\r\n"
                    )
                else:
                    time.sleep(0.1)  # Brief pause on error

                # Small delay to prevent overwhelming the ESP32
                time.sleep(0.1)  # ~10 FPS

            except Exception as e:
                print(f"Stream error: {e}")
                break

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/info")
def server_info():
    """Server status and configuration"""
    return jsonify(
        {
            "camera_active": camera_server.picam2 is not None,
            "face_detection": camera_server.face_detection_enabled,
            "detected_faces": len(camera_server.detected_faces),
            "resolution": "320x240",
            "format": "JPEG",
            "usage": {
                "esp32_recommended": "GET /frame",
                "browser_stream": "GET /stream",
            },
        }
    )


def main():
    print("=== Flask HTTP Camera Server for ESP32 ===")
    print("Resolution: 320x240 JPEG")
    print("ESP32 endpoint: http://your-pi-ip:5000/frame")

    # Parse arguments
    face_detection = False
    port = 5000

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg in ["--face-detection", "-f"]:
                face_detection = True
            elif arg.startswith("--port="):
                port = int(arg.split("=")[1])

    try:
        # Initialize camera
        camera_server.initialize_camera()

        # Enable face detection if requested
        if face_detection:
            camera_server.enable_face_detection()

        print(f"Starting server on port {port}...")
        print(
            f"Face detection: {'ENABLED' if camera_server.face_detection_enabled else 'DISABLED'}"
        )
        print("\nEndpoints:")
        print(f"  Single frame (ESP32): http://0.0.0.0:{port}/frame")
        print(f"  MJPEG stream:         http://0.0.0.0:{port}/stream")
        print(f"  Server info:          http://0.0.0.0:{port}/info")

        # Force garbage collection
        gc.collect()

        # Start Flask server
        app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        camera_server.cleanup()
        print("Camera server shutdown complete")


if __name__ == "__main__":
    main()
