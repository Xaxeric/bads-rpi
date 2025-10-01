#!/usr/bin/python3
"""
Stream Routes Module
Handles MJPEG streaming endpoints
"""

from flask import Blueprint, Response
import time
import sys
import os

# Add core directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from camera_server import get_camera_server

# Create Blueprint for stream routes
stream_bp = Blueprint('stream', __name__)


@stream_bp.route("/stream")
def mjpeg_stream():
    """MJPEG stream - for browsers or advanced ESP32 implementations"""
    
    def generate():
        camera_server = get_camera_server()
        
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


@stream_bp.route("/stream_gray")
def mjpeg_stream_grayscale():
    """MJPEG grayscale stream - memory efficient for ESP32"""
    
    def generate():
        camera_server = get_camera_server()
        
        while True:
            try:
                jpeg_data = camera_server.capture_grayscale_jpeg()
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
                print(f"Grayscale stream error: {e}")
                break

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@stream_bp.route("/stream_compressed")
def mjpeg_stream_compressed():
    """MJPEG compressed stream - ultra-low bandwidth for ESP32"""
    
    def generate():
        camera_server = get_camera_server()
        
        while True:
            try:
                jpeg_data = camera_server.capture_compressed_jpeg()
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

                # Slightly longer delay for compressed stream
                time.sleep(0.15)  # ~6-7 FPS

            except Exception as e:
                print(f"Compressed stream error: {e}")
                break

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")