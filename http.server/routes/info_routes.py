#!/usr/bin/python3
"""
Info Routes Module
Handles server information and status endpoints
"""

from flask import Blueprint, jsonify
import time
import sys
import os

# Add core directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from camera_server import get_camera_server

# Create Blueprint for info routes
info_bp = Blueprint("info", __name__)


@info_bp.route("/")
def index():
    """Basic info page"""
    camera_server = get_camera_server()

    return jsonify(
        {
            "server": "Flask Camera Server for ESP32",
            "resolution": "320x240",
            "endpoints": {
                "single_frame": "/frame",
                "grayscale_frame": "/frame_gray",
                "compressed_frame": "/frame_compressed",
                "mjpeg_stream": "/stream",
                "mjpeg_stream_gray": "/stream_gray",
                "mjpeg_stream_compressed": "/stream_compressed",
                "server_info": "/info",
                "health_check": "/health",
            },
            "face_detection": camera_server.face_detection_enabled,
            "grayscale_processing": camera_server.grayscale_enabled,
            "advanced_compression": camera_server.compression_handler is not None,
        }
    )


@info_bp.route("/info")
def server_info():
    """Server status and configuration"""
    camera_server = get_camera_server()
    status = camera_server.get_server_status()

    return jsonify(
        {
            **status,
            "usage": {
                "esp32_recommended": "GET /frame",
                "esp32_grayscale": "GET /frame_gray",
                "esp32_compressed": "GET /frame_compressed",
                "browser_stream": "GET /stream",
                "browser_stream_gray": "GET /stream_gray",
                "browser_stream_compressed": "GET /stream_compressed",
            },
        }
    )


@info_bp.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    camera_server = get_camera_server()

    # Simple health check
    is_healthy = camera_server.picam2 is not None

    response_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "camera_initialized": is_healthy,
        "timestamp": int(time.time()),
    }

    status_code = 200 if is_healthy else 503
    return jsonify(response_data), status_code
