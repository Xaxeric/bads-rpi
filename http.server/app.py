#!/usr/bin/python3
"""
Modular Flask HTTP Camera Server for ESP32
All features enabled by default for optimal ESP32 integration
"""

import sys
import gc
from flask import Flask

# Import route blueprints
from routes import frame_bp, stream_bp, info_bp
from core.camera_server import get_camera_server


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Register blueprints (routes)
    app.register_blueprint(frame_bp)
    app.register_blueprint(stream_bp)
    app.register_blueprint(info_bp)

    return app


def initialize_features(port=5000):
    """Initialize camera server with all features enabled"""
    camera_server = get_camera_server()

    # Initialize camera
    camera_server.initialize_camera()

    # Enable all features by default
    camera_server.enable_face_detection()
    camera_server.enable_grayscale()
    camera_server.enable_compression()

    return {
        "port": port,
        "face_detection": camera_server.face_detection_enabled,
        "grayscale_processing": camera_server.grayscale_enabled,
        "advanced_compression": camera_server.compression_handler is not None,
    }


def print_server_info(config):
    """Print server information and available endpoints"""
    print("=== Modular Flask HTTP Camera Server for ESP32 ===")
    print("Resolution: 320x240 JPEG")
    print("All features enabled by default")
    print(f"ESP32 endpoint: http://your-pi-ip:{config['port']}/frame")
    print(f"Starting server on port {config['port']}...")

    # Feature status
    print(f"Face detection: {'ENABLED' if config['face_detection'] else 'DISABLED'}")
    print(
        f"Grayscale processing: {'ENABLED' if config['grayscale_processing'] else 'DISABLED'}"
    )
    print(
        f"Advanced compression: {'ENABLED' if config['advanced_compression'] else 'DISABLED'}"
    )

    # Endpoints
    print("\nFrame Endpoints:")
    print(f"  Single frame (ESP32):     http://0.0.0.0:{config['port']}/frame")
    print(f"  Grayscale frame (ESP32):  http://0.0.0.0:{config['port']}/frame_gray")
    print(
        f"  Compressed frame (ESP32): http://0.0.0.0:{config['port']}/frame_compressed"
    )

    print("\nStream Endpoints:")
    print(f"  MJPEG stream:             http://0.0.0.0:{config['port']}/stream")
    print(f"  MJPEG stream (gray):      http://0.0.0.0:{config['port']}/stream_gray")
    print(
        f"  MJPEG stream (compressed): http://0.0.0.0:{config['port']}/stream_compressed"
    )

    print("\nInfo Endpoints:")
    print(f"  Server info:              http://0.0.0.0:{config['port']}/info")
    print(f"  Health check:             http://0.0.0.0:{config['port']}/health")


def main():
    """Main application entry point"""
    try:
        # Get port from command line if provided, otherwise use default
        port = 5000
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            port = int(sys.argv[1])

        # Initialize camera and features (all enabled by default)
        config = initialize_features(port)

        # Print server information
        print_server_info(config)

        # Force garbage collection
        gc.collect()

        # Create and start Flask app
        app = create_app()
        app.run(host="0.0.0.0", port=config["port"], debug=False, threaded=True)

    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        camera_server = get_camera_server()
        camera_server.cleanup()
        print("Camera server shutdown complete")


if __name__ == "__main__":
    main()
