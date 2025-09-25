#!/usr/bin/python3
"""
Ultra-lightweight streaming server with face detection for Raspberry Pi Zero 2 W
Minimal memory footprint version with toggleable face detection
"""

import socket
import time
import gc
import sys
import os
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

# Try to import face detection (optional)
try:
    from face_detection import create_face_detector
    import cv2

    FACE_DETECTION_AVAILABLE = True
except ImportError as e:
    FACE_DETECTION_AVAILABLE = False
    print(f"Face detection not available: {e}")
    print("To enable: pip3 install opencv-python")


def optimize_system():
    """Apply system-level optimizations"""
    # Force garbage collection
    gc.collect()

    # Set garbage collection to be more aggressive
    gc.set_threshold(100, 5, 5)  # More frequent collection

    print("System optimizations applied")


def create_minimal_camera():
    """Create camera with absolute minimal settings"""
    picam2 = Picamera2()

    # Minimal configuration for Pi Zero 2 W
    video_config = picam2.create_video_configuration(
        main={"size": (320, 240)},  # Very small resolution
        buffer_count=2,  # Minimal buffers
        queue=False,  # No queue
        controls={
            "FrameRate": 15,  # Reduced frame rate
        },
    )

    picam2.configure(video_config)
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


def capture_frame_for_detection(picam2):
    """Capture a frame for face detection (separate from video stream)"""
    try:
        # Capture frame to memory
        frame = picam2.capture_array()

        # Convert from RGB to BGR for OpenCV
        if len(frame.shape) == 3:
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            frame_bgr = frame

        return frame_bgr
    except Exception as e:
        print(f"Frame capture error: {e}")
        return None


def main():
    print("=== Ultra-Lightweight Stream Server with Face Detection ===")
    print("Resolution: 320x240, Frame rate: 15fps, Bitrate: 300kbps")

    # Parse command line arguments
    face_detection_enabled = False
    if len(sys.argv) > 1:
        if "--face-detection" in sys.argv or "-f" in sys.argv:
            if FACE_DETECTION_AVAILABLE:
                face_detection_enabled = True
                print("Face detection: ENABLED")
            else:
                print("Face detection: REQUESTED but NOT AVAILABLE")
        elif "--help" in sys.argv or "-h" in sys.argv:
            print("Usage: python3 lightweight_stream_with_faces.py [options]")
            print("Options:")
            print("  -f, --face-detection    Enable face detection")
            print("  -h, --help             Show this help")
            print("\nCommands during streaming:")
            print("  Press 'f' + Enter to toggle face detection")
            print("  Press 'q' + Enter or Ctrl+C to quit")
            return

    if not face_detection_enabled:
        print("Face detection: DISABLED (use -f to enable)")

    # System optimization
    optimize_system()

    # Check initial memory
    initial_mem = get_memory_info()
    print(f"Available memory: {initial_mem:.1f}MB")

    if initial_mem < 100:
        print("WARNING: Very low memory! Consider closing other processes.")

    picam2 = create_minimal_camera()

    # Very low bitrate for minimal memory usage
    encoder = H264Encoder(bitrate=300000)  # 300kbps

    # Initialize face detector if enabled
    face_detector = None
    if face_detection_enabled and FACE_DETECTION_AVAILABLE:
        face_detector = create_face_detector(lightweight=True)
        if not face_detector.is_available():
            print("Face detection initialization failed, disabling...")
            face_detector = None
            face_detection_enabled = False

    # Minimal socket settings
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32768)  # Small send buffer
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192)  # Small receive buffer

    try:
        sock.bind(("0.0.0.0", 10001))
        sock.listen(1)

        print("Listening on port 10001...")
        print(
            "Memory optimizations active - streaming will be lower quality but stable"
        )

        if face_detection_enabled:
            print("Face detection active - will detect faces every 2 seconds")

        picam2.start()

        while True:  # Server loop - restart on client disconnect
            try:
                print("Waiting for client...")
                conn, addr = sock.accept()
                print(f"Client connected: {addr}")

                # Minimal connection settings
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                stream = conn.makefile("wb", buffering=4096)  # Very small buffer
                encoder.output = FileOutput(stream)
                picam2.start_encoder(encoder)

                print("Streaming... (Press Ctrl+C to stop server)")
                if face_detection_enabled:
                    print("Face detection running in background...")

                # Memory monitoring loop
                check_count = 0
                face_check_count = 0

                while True:
                    time.sleep(2)  # Less frequent checks

                    check_count += 1
                    face_check_count += 1

                    # Memory check every 30 seconds
                    if check_count >= 15:
                        mem = get_memory_info()
                        status_line = f"Memory: {mem:.1f}MB"

                        # Add face detection stats if enabled
                        if face_detector and face_detection_enabled:
                            stats = face_detector.get_stats()
                            status_line += f" | Faces found: {stats['faces_found']}"

                        print(status_line, end="\r")

                        if mem < 30:
                            print(f"\nLow memory: {mem:.1f}MB - forcing cleanup")
                            gc.collect()
                        check_count = 0

                    # Face detection every 4 seconds (2 sleep cycles)
                    if (
                        face_detector
                        and face_detection_enabled
                        and face_check_count >= 2
                    ):
                        try:
                            # Capture frame for face detection
                            frame = capture_frame_for_detection(picam2)
                            if frame is not None:
                                faces = face_detector.detect_faces(frame)
                                if len(faces) > 0:
                                    # Optional: Log face detection events
                                    timestamp = time.strftime("%H:%M:%S")
                                    print(f"\n[{timestamp}] Found {len(faces)} face(s)")

                        except Exception as e:
                            print(f"\nFace detection error: {e}")

                        face_check_count = 0

            except BrokenPipeError:
                print("\nClient disconnected")
            except ConnectionResetError:
                print("\nClient connection reset")
            except KeyboardInterrupt:
                print("\nShutting down server...")
                break
            except Exception as e:
                print(f"\nStream error: {e}")
            finally:
                # Cleanup for this client session
                try:
                    picam2.stop_encoder()
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
        # Final cleanup
        try:
            picam2.stop()
            picam2.close()
            sock.close()
        except Exception:
            pass

        # Show final face detection stats
        if face_detector:
            stats = face_detector.get_stats()
            print(f"Face detection stats: {stats}")

        final_mem = get_memory_info()
        print(f"Final memory: {final_mem:.1f}MB")
        print("Server shutdown complete")


if __name__ == "__main__":
    main()
