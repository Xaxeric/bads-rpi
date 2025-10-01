#!/usr/bin/python3
"""
Frame Routes Module
Handles all single frame capture endpoints
"""

from flask import Blueprint, Response
import sys
import os

# Add core directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from camera_server import get_camera_server

# Create Blueprint for frame routes
frame_bp = Blueprint("frame", __name__)

# Common headers for frame responses
FRAME_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


@frame_bp.route("/frame")
def get_frame():
    """Get a single JPEG frame - perfect for ESP32"""
    try:
        camera_server = get_camera_server()
        jpeg_data = camera_server.capture_jpeg()

        if jpeg_data and len(jpeg_data) > 0:
            headers = FRAME_HEADERS.copy()
            headers["Content-Length"] = str(len(jpeg_data))

            return Response(
                jpeg_data,
                mimetype="image/jpeg",
                headers=headers,
            )
        else:
            print("No camera data available")
            return Response("Camera not available", status=503, mimetype="text/plain")
    except Exception as e:
        print(f"Frame route error: {e}")
        return Response(f"Server error: {e}", status=500, mimetype="text/plain")


@frame_bp.route("/frame_gray")
def get_frame_grayscale():
    """Get a single grayscale JPEG frame - optimized for ESP32"""
    try:
        camera_server = get_camera_server()
        jpeg_data = camera_server.capture_grayscale_jpeg()

        if jpeg_data and len(jpeg_data) > 0:
            headers = FRAME_HEADERS.copy()
            headers["Content-Length"] = str(len(jpeg_data))

            return Response(
                jpeg_data,
                mimetype="image/jpeg",
                headers=headers,
            )
        else:
            print("No grayscale camera data available")
            return Response("Camera not available", status=503, mimetype="text/plain")
    except Exception as e:
        print(f"Grayscale frame route error: {e}")
        return Response(f"Server error: {e}", status=500, mimetype="text/plain")


@frame_bp.route("/frame_compressed")
def get_frame_compressed():
    """Get a highly compressed frame for ESP32 with limited memory"""
    try:
        camera_server = get_camera_server()
        jpeg_data = camera_server.capture_compressed_jpeg()

        if jpeg_data and len(jpeg_data) > 0:
            headers = FRAME_HEADERS.copy()
            headers["Content-Length"] = str(len(jpeg_data))

            return Response(
                jpeg_data,
                mimetype="image/jpeg",
                headers=headers,
            )
        else:
            print("No compressed camera data available")
            return Response("Camera not available", status=503, mimetype="text/plain")
    except Exception as e:
        print(f"Compressed frame route error: {e}")
        return Response(f"Server error: {e}", status=500, mimetype="text/plain")
