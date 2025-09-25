#!/usr/bin/python3

import socket
import sys
import threading
import queue
import time


class MJPEGStreamClient:
    def __init__(self, server_ip, server_port=10001):
        self.server_ip = server_ip
        self.server_port = server_port
        self.frame_queue = queue.Queue(maxsize=10)
        self.running = False
        self.sock = None

    def find_jpeg_boundaries(self, buffer):
        """Find JPEG frame boundaries in the buffer"""
        jpeg_start = b"\xff\xd8"  # JPEG start marker
        jpeg_end = b"\xff\xd9"  # JPEG end marker

        frames = []
        search_pos = 0

        while search_pos < len(buffer):
            # Find start of JPEG
            start_pos = buffer.find(jpeg_start, search_pos)
            if start_pos == -1:
                break

            # Find end of this JPEG
            end_pos = buffer.find(jpeg_end, start_pos + 2)
            if end_pos == -1:
                break

            # Extract complete JPEG frame
            end_pos += 2  # Include the end marker
            jpeg_frame = buffer[start_pos:end_pos]
            frames.append(jpeg_frame)

            search_pos = end_pos

        # Return frames and remaining buffer
        if frames:
            last_end = buffer.rfind(jpeg_end) + 2
            remaining_buffer = buffer[last_end:]
            return frames, remaining_buffer
        else:
            return [], buffer

    def receive_stream(self):
        """Receive MJPEG stream from server"""
        try:
            print(f"Connecting to {self.server_ip}:{self.server_port}...")

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_ip, self.server_port))
                print("Connected! Receiving MJPEG stream...")

                # Create a buffer to accumulate MJPEG data
                buffer = b""

                while self.running:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            break

                        buffer += data

                        # Extract complete JPEG frames
                        frames, buffer = self.find_jpeg_boundaries(buffer)

                        for frame in frames:
                            # Add to frame queue if not full
                            if not self.frame_queue.full():
                                self.frame_queue.put(frame)

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

    def save_stream(self, save_file=None):
        """Save the received MJPEG stream"""
        if save_file is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_file = f"received_mjpeg_{timestamp}.mjpeg"

        print(f"Saving MJPEG stream to: {save_file}")

        frame_count = 0
        total_size = 0

        with open(save_file, "wb") as f:
            while self.running or not self.frame_queue.empty():
                try:
                    # Get frame data from queue
                    frame_data = self.frame_queue.get(timeout=1.0)

                    # Write JPEG frame
                    f.write(frame_data)

                    frame_count += 1
                    total_size += len(frame_data)

                    # Show progress
                    if frame_count % 10 == 0:
                        print(
                            f"Received {frame_count} frames ({total_size / 1024:.1f} KB)",
                            end="\r",
                        )

                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Save error: {e}")
                    break

        print(f"\nReceived {frame_count} MJPEG frames")
        print(f"Total size: {total_size / 1024:.1f} KB")
        print(f"Stream saved to: {save_file}")
        return save_file

    def display_frames_as_images(self, max_frames=10):
        """Save first few frames as individual JPEG images"""
        print("Saving first few frames as individual JPEG files...")

        frame_count = 0
        saved_count = 0

        while (
            self.running or not self.frame_queue.empty()
        ) and saved_count < max_frames:
            try:
                frame_data = self.frame_queue.get(timeout=1.0)

                # Save as individual JPEG
                filename = f"frame_{saved_count:04d}.jpg"
                with open(filename, "wb") as f:
                    f.write(frame_data)

                saved_count += 1
                frame_count += 1
                print(f"Saved frame {saved_count}/{max_frames}: {filename}")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Frame save error: {e}")
                break

        # Continue counting remaining frames
        while self.running or not self.frame_queue.empty():
            try:
                self.frame_queue.get(timeout=1.0)
                frame_count += 1
            except queue.Empty:
                break

        print(f"Total frames processed: {frame_count}")

    def start_streaming(self, mode="save", save_file=None, max_frames=10):
        """Start receiving the stream"""
        self.running = True

        # Start receiver thread
        receiver_thread = threading.Thread(target=self.receive_stream)
        receiver_thread.daemon = True
        receiver_thread.start()

        try:
            if mode == "save":
                return self.save_stream(save_file)
            elif mode == "images":
                self.display_frames_as_images(max_frames)
            else:
                # Just receive and count
                frame_count = 0
                while self.running:
                    try:
                        self.frame_queue.get(timeout=1.0)
                        frame_count += 1
                        print(f"Received frame {frame_count}", end="\r")
                    except queue.Empty:
                        continue

        except KeyboardInterrupt:
            print("\nStopping stream...")
        finally:
            self.running = False
            receiver_thread.join(timeout=2)


def main():
    """Main function with command line argument handling"""

    if len(sys.argv) < 2:
        print("Usage: python3 mjpeg_client.py <server_ip> [mode] [filename]")
        print("Example: python3 mjpeg_client.py 192.168.18.66")
        print("Example: python3 mjpeg_client.py 192.168.18.66 save video.mjpeg")
        print("Example: python3 mjpeg_client.py 192.168.18.66 images")
        print("\nModes:")
        print("  save    - Save as MJPEG file (default)")
        print("  images  - Save first 10 frames as individual JPEGs")
        print("  count   - Just receive and count frames")
        print("\nNote: This client is for MJPEG streams from stream_with_overlay.py")
        sys.exit(1)

    server_ip = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "save"
    save_file = sys.argv[3] if len(sys.argv) > 3 else None

    # Validate IP address format
    try:
        socket.inet_aton(server_ip)
    except socket.error:
        print(f"Error: '{server_ip}' is not a valid IP address")
        sys.exit(1)

    # Validate mode
    if mode not in ["save", "images", "count"]:
        print(f"Error: Invalid mode '{mode}'. Use 'save', 'images', or 'count'")
        sys.exit(1)

    print(f"MJPEG Client - Mode: {mode}")

    # Create and start stream client
    client = MJPEGStreamClient(server_ip)

    if mode == "save":
        output_file = client.start_streaming(mode, save_file)
        print(f"\nTo view the saved stream:")
        print(f"  vlc {output_file}")
        print(f"  ffplay {output_file}")
    else:
        client.start_streaming(mode)


if __name__ == "__main__":
    main()
