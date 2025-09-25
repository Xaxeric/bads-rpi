#!/usr/bin/python3

import socket
import sys
import threading
import queue


class StreamClient:
    def __init__(self, server_ip, server_port=10001):
        self.server_ip = server_ip
        self.server_port = server_port
        self.frame_queue = queue.Queue(maxsize=10)
        self.running = False
        self.sock = None

    def receive_stream(self):
        """Receive H.264 stream from server and decode frames"""
        try:
            print(f"Connecting to {self.server_ip}:{self.server_port}...")

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_ip, self.server_port))
                print("Connected! Receiving video stream...")

                # Create a buffer to accumulate H.264 data
                buffer = b""

                while self.running:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            break

                        buffer += data

                        # Try to find H.264 frame boundaries (NAL units)
                        # H.264 NAL units start with 0x00000001 or 0x000001
                        while len(buffer) > 4:
                            # Look for NAL unit start codes
                            start_code_4 = buffer.find(b"\x00\x00\x00\x01")
                            start_code_3 = buffer.find(b"\x00\x00\x01")

                            if start_code_4 != -1 and (
                                start_code_3 == -1 or start_code_4 < start_code_3
                            ):
                                start_pos = start_code_4 + 4
                                next_start = buffer.find(b"\x00\x00\x00\x01", start_pos)
                                if next_start == -1:
                                    next_start = buffer.find(b"\x00\x00\x01", start_pos)
                            elif start_code_3 != -1:
                                start_pos = start_code_3 + 3
                                next_start = buffer.find(b"\x00\x00\x01", start_pos)
                                if next_start == -1:
                                    next_start = buffer.find(
                                        b"\x00\x00\x00\x01", start_pos
                                    )
                            else:
                                break

                            if next_start != -1:
                                # Extract one NAL unit
                                nal_unit = buffer[:next_start]
                                buffer = buffer[next_start:]

                                # Add to frame queue if not full
                                if not self.frame_queue.full():
                                    self.frame_queue.put(nal_unit)
                            else:
                                break

                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"Error receiving data: {e}")
                        break

        except ConnectionRefusedError:
            print(f"Error: Could not connect to {self.server_ip}:{self.server_port}")
            print("Make sure the server is running and the IP address is correct.")
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.running = False

    def display_stream(self):
        """Display the received video stream using OpenCV"""
        print("Starting video display...")

        # For this simple example, we'll save frames to a temporary file
        # and try to read them back (H.264 direct decoding is complex)
        temp_file = "temp_stream.h264"

        frame_count = 0

        while self.running or not self.frame_queue.empty():
            try:
                # Get frame data from queue
                frame_data = self.frame_queue.get(timeout=1.0)

                # Write to temporary file
                with open(temp_file, "ab") as f:
                    f.write(frame_data)

                frame_count += 1
                print(f"Received frame {frame_count}", end="\r")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Display error: {e}")
                break

        print(f"\nReceived {frame_count} frame segments")
        print(f"Stream data saved to: {temp_file}")

    def start_streaming(self, save_file=None):
        """Start receiving and displaying the stream"""
        self.running = True

        # Start receiver thread
        receiver_thread = threading.Thread(target=self.receive_stream)
        receiver_thread.daemon = True
        receiver_thread.start()

        try:
            # Run display in main thread
            self.display_stream()

        except KeyboardInterrupt:
            print("\nStopping stream...")
        finally:
            self.running = False
            receiver_thread.join(timeout=2)

            if save_file:
                import shutil

                shutil.move("temp_stream.h264", save_file)
                print(f"Stream saved as: {save_file}")


def main():
    """Main function with command line argument handling"""

    if len(sys.argv) < 2:
        print("Usage: python3 realtime_client.py <server_ip> [save_file.h264]")
        print("Example: python3 realtime_client.py 192.168.1.100")
        print("Example: python3 realtime_client.py 192.168.1.100 captured_video.h264")
        print("\nNote: This client receives the H.264 stream in real-time.")
        print("Press Ctrl+C to stop receiving.")
        sys.exit(1)

    server_ip = sys.argv[1]
    save_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Validate IP address format
    try:
        socket.inet_aton(server_ip)
    except socket.error:
        print(f"Error: '{server_ip}' is not a valid IP address")
        sys.exit(1)

    # Create and start stream client
    client = StreamClient(server_ip)
    client.start_streaming(save_file)

    print("\nTo play the received video:")
    filename = save_file or "temp_stream.h264"
    print(f"  vlc {filename}")
    print(f"  ffplay {filename}")
    print(f"  mpv {filename}")


if __name__ == "__main__":
    main()
