#!/usr/bin/python3
"""
Core Camera Server Module
Handles camera initialization and frame processing
"""

import os
import sys
import time
import cv2
from picamera2 import Picamera2
import threading

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lib"))

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


class CameraServer:
    """
    Core camera server handling all camera operations
    Follows Single Responsibility Principle - only handles camera functionality
    """
    
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

    def capture_grayscale_jpeg(self):
        """Capture a grayscale JPEG frame using grayscale handler"""
        try:
            with self.lock:
                # Capture frame
                frame = self.picam2.capture_array()

                # Convert RGB to BGR
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Add face detection if enabled
                if self.face_detection_enabled:
                    bgr_frame = self.process_frame_with_faces(bgr_frame)

                # Convert to grayscale using handler if available
                if self.grayscale_handler:
                    jpeg_data = self.grayscale_handler.get_grayscale_jpeg(
                        bgr_frame, quality=80
                    )
                    return jpeg_data
                else:
                    # Fallback to basic grayscale
                    gray_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
                    gray_3ch = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

                    encode_param = [cv2.IMWRITE_JPEG_QUALITY, 80]
                    success, jpeg_buffer = cv2.imencode(".jpg", gray_3ch, encode_param)

                    if success:
                        return jpeg_buffer.tobytes()
                    else:
                        return None

        except Exception as e:
            print(f"Grayscale capture error: {e}")
            return None

    def capture_compressed_jpeg(self):
        """Capture a highly compressed JPEG frame for ESP32"""
        try:
            with self.lock:
                # Capture frame
                frame = self.picam2.capture_array()

                # Convert RGB to BGR
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Add face detection if enabled
                if self.face_detection_enabled:
                    bgr_frame = self.process_frame_with_faces(bgr_frame)

                # Use compression handler if available
                if self.compression_handler:
                    # Target 8KB for ESP32 with limited memory
                    compressed_data = self.compression_handler.compress_for_esp32(
                        bgr_frame, target_size_kb=8
                    )
                    return compressed_data
                else:
                    # Fallback to basic high compression
                    encode_param = [cv2.IMWRITE_JPEG_QUALITY, 50]
                    success, jpeg_buffer = cv2.imencode(".jpg", bgr_frame, encode_param)

                    if success:
                        return jpeg_buffer.tobytes()
                    else:
                        return None

        except Exception as e:
            print(f"Compressed capture error: {e}")
            return None

    def get_server_status(self):
        """Get current server status for info endpoints"""
        return {
            "camera_active": self.picam2 is not None,
            "face_detection": self.face_detection_enabled,
            "grayscale_processing": self.grayscale_enabled,
            "advanced_compression": self.compression_handler is not None,
            "detected_faces": len(self.detected_faces),
            "resolution": "320x240",
            "format": "JPEG",
        }

    def cleanup(self):
        """Clean up camera resources"""
        if self.picam2:
            try:
                self.picam2.stop()
            except Exception:
                pass


# Global camera server instance - Singleton pattern
_camera_server_instance = None

def get_camera_server():
    """Get the global camera server instance (Singleton pattern)"""
    global _camera_server_instance
    if _camera_server_instance is None:
        _camera_server_instance = CameraServer()
    return _camera_server_instance