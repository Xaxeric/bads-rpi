#!/usr/bin/python3
"""
Simple test client for Flask HTTP Camera Server
Tests the /frame endpoint and saves images
"""

import requests
import time
import sys


def test_http_server(server_ip="localhost", port=5000, num_frames=10):
    """Test the HTTP camera server"""

    base_url = f"http://{server_ip}:{port}"

    print(f"Testing HTTP Camera Server at {base_url}")
    print("=" * 50)

    # Test server info endpoint
    try:
        print("1. Testing server info...")
        response = requests.get(f"{base_url}/info", timeout=5)
        if response.status_code == 200:
            info = response.json()
            print(f"   ✓ Server info: {info}")
        else:
            print(f"   ✗ Info endpoint error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Info endpoint failed: {e}")

    print()

    # Test frame endpoint
    print(f"2. Testing frame endpoint ({num_frames} frames)...")

    successful_frames = 0
    total_bytes = 0

    for i in range(num_frames):
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/frame", timeout=10)
            request_time = time.time() - start_time

            if response.status_code == 200:
                frame_size = len(response.content)
                total_bytes += frame_size
                successful_frames += 1

                # Save frame
                filename = f"test_frame_{i + 1:03d}.jpg"
                with open(filename, "wb") as f:
                    f.write(response.content)

                print(
                    f"   Frame {i + 1:2d}: ✓ {frame_size:5d} bytes, {request_time:.2f}s -> {filename}"
                )

            else:
                print(f"   Frame {i + 1:2d}: ✗ HTTP {response.status_code}")

        except Exception as e:
            print(f"   Frame {i + 1:2d}: ✗ Error: {e}")

        # Small delay between requests
        time.sleep(0.5)

    print()
    print("Results:")
    print(f"  Successful frames: {successful_frames}/{num_frames}")
    print(f"  Total data: {total_bytes} bytes")
    if successful_frames > 0:
        print(f"  Average frame size: {total_bytes / successful_frames:.1f} bytes")


def main():
    """Main function with command line arguments"""

    server_ip = "localhost"
    port = 5000
    num_frames = 10

    # Parse command line arguments
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    if len(sys.argv) > 3:
        num_frames = int(sys.argv[3])

    print("HTTP Camera Server Test Client")
    print(f"Usage: {sys.argv[0]} [server_ip] [port] [num_frames]")
    print(f"Testing: {server_ip}:{port} ({num_frames} frames)")
    print()

    test_http_server(server_ip, port, num_frames)


if __name__ == "__main__":
    main()
