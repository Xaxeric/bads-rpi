#!/usr/bin/python3
"""
Ultra-lightweight streaming server for Raspberry Pi Zero 2 W
Minimal memory footprint version
"""

import socket
import time
import gc
import os  # noqa: F401
from picamera2 import Picamera2 # pyright: ignore[reportMissingImports]
from picamera2.encoders import H264Encoder # pyright: ignore[reportMissingImports]
from picamera2.outputs import FileOutput # pyright: ignore[reportMissingImports]


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
    except:
        return 0


def main():
    print("=== Ultra-Lightweight Stream Server ===")
    print("Resolution: 480x320, Frame rate: 15fps, Bitrate: 300kbps")

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

                # Memory monitoring loop
                check_count = 0
                while True:
                    time.sleep(2)  # Less frequent checks

                    check_count += 1
                    if check_count >= 15:  # Check memory every 30 seconds
                        mem = get_memory_info()
                        print(f"Memory: {mem:.1f}MB", end="\r")
                        if mem < 30:
                            print(f"\nLow memory: {mem:.1f}MB - forcing cleanup")
                            gc.collect()
                        check_count = 0

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
                except:
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
        except:
            pass

        final_mem = get_memory_info()
        print(f"Final memory: {final_mem:.1f}MB")
        print("Server shutdown complete")


if __name__ == "__main__":
    main()
