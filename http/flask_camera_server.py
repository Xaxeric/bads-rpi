#!/usr/bin/python3
"""
Flask HTTP Camera Server for ESP32
Optimized for ESP32 with 320x240 JPEG streaming
"""

import os
import sys
import time
import cv2
import requests
from flask import Flask, Response, jsonify
from picamera2 import Picamera2
import threading
import gc

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

try:
    from face_detection import create_face_detector
    from grayscale_handler import create_grayscale_handler
    from compression_handler import create_compression_handler

    FACE_DETECTION_AVAILABLE = True
    GRAYSCALE_HANDLER_AVAILABLE = True
    COMPRESSION_HANDLER_AVAILABLE = True
except ImportError as e:
    FACE_DETECTION_AVAILABLE = False
    GRAYSCALE_HANDLER_AVAILABLE = False
    COMPRESSION_HANDLER_AVAILABLE = False
    print(f"Extended features not available: {e}")

app = Flask(__name__)

# Database server configuration
DATABASE_SERVER_IP = "192.168.18.11"
DATABASE_SERVER_PORT = 3000
DATABASE_URL = f"http://{DATABASE_SERVER_IP}:{DATABASE_SERVER_PORT}/api/capture"


class CameraServer:
    def __init__(self):
        self.picam2 = None
        self.face_detector = None
        self.grayscale_handler = None
        self.compression_handler = None
        self.detected_faces = []
        self.last_detection_time = 0
        self.detection_interval = 2.0
        self.face_detection_enabled = False
        self.grayscale_enabled = False
        self.lock = threading.Lock()

    def send_frame_to_database(self, jpeg_data):
        """Send grayscale frame data to database server"""
        try:
            # Prepare the file data for multipart/form-data
            files = {"image": ("frame.jpg", jpeg_data, "image/jpeg")}

            # Optional: Add additional data as form fields
            data = {
                "timestamp": str(time.time()),
                "format": "jpeg",
                "grayscale": "true",
                "resolution": "320x240",
            }

            # Send to database server with timeout using form-data
            response = requests.post(DATABASE_URL, files=files, data=data, timeout=5)

            if response.status_code == 200:
                print("Frame sent to database successfully")
            else:
                print(f"Database server responded with status: {response.status_code}")

        except requests.exceptions.Timeout:
            print("Timeout sending frame to database server")
        except requests.exceptions.ConnectionError:
            print(
                f"Could not connect to database server at {DATABASE_SERVER_IP}:{DATABASE_SERVER_PORT}"
            )
        except Exception as e:
            print(f"Error sending frame to database: {e}")

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

    def enable_grayscale(self):
        """Enable grayscale processing if available"""
        if GRAYSCALE_HANDLER_AVAILABLE:
            self.grayscale_handler = create_grayscale_handler(esp32_optimized=True)
            self.grayscale_enabled = True
            print("Grayscale processing enabled")
        else:
            print("Grayscale handler not available")

    def enable_compression(self):
        """Enable advanced compression if available"""
        if COMPRESSION_HANDLER_AVAILABLE:
            self.compression_handler = create_compression_handler(esp32_optimized=True)
            print("Advanced compression enabled")
        else:
            print("Compression handler not available")

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

    def process_frame_with_faces_on_grayscale(self, gray_single_channel, gray_frame_bgr):
        """Optimized face detection on grayscale image"""
        current_time = time.time()

        # Run face detection periodically on grayscale image (more efficient)
        if (
            self.face_detector
            and (current_time - self.last_detection_time) > self.detection_interval
        ):
            # Use grayscale image directly for face detection
            faces = self.face_detector.detect_faces(gray_single_channel)

            if len(faces) > 0:
                # Keep only the largest face for better performance
                largest_face = max(faces, key=lambda face: face[2] * face[3])
                self.detected_faces = [largest_face]
                print(f"Face detected: {largest_face}")
            else:
                self.detected_faces = []

            self.last_detection_time = current_time

        # Draw face boxes on the 3-channel grayscale image
        if len(self.detected_faces) > 0:
            for x, y, w, h in self.detected_faces:
                cv2.rectangle(gray_frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    gray_frame_bgr,
                    "FACE",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                )

        return gray_frame_bgr

    def capture_jpeg(self):
        """Capture a single JPEG frame with optimized processing flow"""
        try:
            with self.lock:
                # Step 1: Capture frame
                frame = self.picam2.capture_array()

                # Step 2: Convert RGB to BGR for OpenCV processing
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Step 3: Convert to grayscale using grayscale handler
                if self.grayscale_handler:
                    # Use advanced grayscale processing
                    gray_frame_bgr = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
                    gray_frame_bgr = cv2.cvtColor(gray_frame_bgr, cv2.COLOR_GRAY2BGR)
                else:
                    # Fallback to basic grayscale
                    gray_frame_bgr = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
                    gray_frame_bgr = cv2.cvtColor(gray_frame_bgr, cv2.COLOR_GRAY2BGR)

                # Step 4: Send grayscale frame to database in background thread
                gray_encode_param = [cv2.IMWRITE_JPEG_QUALITY, 80]
                gray_success, gray_jpeg_buffer = cv2.imencode(
                    ".jpg", gray_frame_bgr, gray_encode_param
                )
                
                if gray_success:
                    gray_jpeg_data = gray_jpeg_buffer.tobytes()
                    # Send to database in background thread to avoid blocking
                    threading.Thread(
                        target=self.send_frame_to_database,
                        args=(gray_jpeg_data,),
                        daemon=True,
                    ).start()

                # Step 5: Add face detection to grayscale image (more efficient)
                if self.face_detection_enabled:
                    # Apply face detection on the grayscale image
                    gray_single_channel = cv2.cvtColor(gray_frame_bgr, cv2.COLOR_BGR2GRAY)
                    gray_frame_bgr = self.process_frame_with_faces_on_grayscale(gray_single_channel, gray_frame_bgr)

                # Step 6: Compress using compression handler 
                if self.compression_handler:
                    # Use advanced compression handler
                    compressed_data = self.compression_handler.compress_image(
                        gray_frame_bgr, quality=85
                    )
                    if compressed_data:
                        return compressed_data
                    else:
                        # Fallback to basic encoding if compression handler fails
                        encode_param = [cv2.IMWRITE_JPEG_QUALITY, 85]
                        success, jpeg_buffer = cv2.imencode(".jpg", gray_frame_bgr, encode_param)
                        return jpeg_buffer.tobytes() if success else None
                else:
                    # Use basic JPEG encoding
                    encode_param = [cv2.IMWRITE_JPEG_QUALITY, 85]
                    success, jpeg_buffer = cv2.imencode(".jpg", gray_frame_bgr, encode_param)
                    
                    if success:
                        return jpeg_buffer.tobytes()
                    else:
                        print("JPEG encoding failed")
                        return None

        except Exception as e:
            print(f"Capture error: {e}")
            return None

    def capture_grayscale_jpeg_with_faces(self):
        """Capture a grayscale JPEG frame with face detection for streaming"""
        try:
            with self.lock:
                # Capture frame
                frame = self.picam2.capture_array()

                # Convert RGB to BGR
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Convert to grayscale first (more efficient)
                gray_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
                gray_3ch = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

                # Apply face detection on grayscale (more efficient)
                if self.face_detection_enabled:
                    gray_3ch = self.process_frame_with_faces_on_grayscale(gray_frame, gray_3ch)

                # Convert to JPEG using handler if available
                if self.grayscale_handler:
                    jpeg_data = self.grayscale_handler.get_grayscale_jpeg(
                        gray_3ch, quality=80
                    )
                else:
                    # Fallback to basic grayscale encoding
                    encode_param = [cv2.IMWRITE_JPEG_QUALITY, 80]
                    success, jpeg_buffer = cv2.imencode(".jpg", gray_3ch, encode_param)

                    if success:
                        jpeg_data = jpeg_buffer.tobytes()
                    else:
                        jpeg_data = None

                # Send frame to database server
                if jpeg_data:
                    # Send to database in background thread to avoid blocking
                    threading.Thread(
                        target=self.send_frame_to_database,
                        args=(jpeg_data,),
                        daemon=True,
                    ).start()

                return jpeg_data

        except Exception as e:
            print(f"Grayscale with faces capture error: {e}")
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
            "grayscale_processing": camera_server.grayscale_enabled,
            "advanced_compression": camera_server.compression_handler is not None,
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
    """MJPEG grayscale stream with face detection - for browsers or advanced ESP32 implementations"""

    def generate():
        while True:
            try:
                jpeg_data = camera_server.capture_grayscale_jpeg_with_faces()
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
            "grayscale_processing": camera_server.grayscale_enabled,
            "advanced_compression": camera_server.compression_handler is not None,
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

    # Fixed port - no arguments
    port = 5000

    try:
        # Initialize camera
        camera_server.initialize_camera()

        # Enable all features by default
        camera_server.enable_face_detection()
        camera_server.enable_grayscale()
        camera_server.enable_compression()

        print(f"Starting server on port {port}...")
        print(
            f"Face detection: {'ENABLED' if camera_server.face_detection_enabled else 'DISABLED'}"
        )
        print(
            f"Grayscale processing: {'ENABLED' if camera_server.grayscale_enabled else 'DISABLED'}"
        )
        print(
            f"Advanced compression: {'ENABLED' if camera_server.compression_handler is not None else 'DISABLED'}"
        )
        print("\nEndpoints:")
        print(f"  Single frame (ESP32):     http://0.0.0.0:{port}/frame")
        print(f"  MJPEG grayscale stream with faces: http://0.0.0.0:{port}/stream")
        print(f"  Server info:              http://0.0.0.0:{port}/info")
        print(f"\nDatabase server: {DATABASE_SERVER_IP}:{DATABASE_SERVER_PORT}")
        print("All captured frames will be sent to database after grayscaling")

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
