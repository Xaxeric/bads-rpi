#!/usr/bin/python3

import socket
import sys
import os
from datetime import datetime

def connect_and_receive_stream(server_ip, server_port=10001, output_file=None):
    """
    Connect to the Raspberry Pi streaming server and receive H.264 video stream
    
    Args:
        server_ip (str): IP address of the Raspberry Pi server
        server_port (int): Port number (default: 10001)
        output_file (str): Output filename for the video (optional)
    """
    
    # Generate default filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"received_stream_{timestamp}.h264"
    
    try:
        print(f"Connecting to {server_ip}:{server_port}...")
        
        # Create socket and connect to server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((server_ip, server_port))
            print("Connected successfully!")
            
            # Open output file for writing binary data
            with open(output_file, 'wb') as f:
                print(f"Receiving video stream and saving to: {output_file}")
                
                # Receive data in chunks
                total_bytes = 0
                chunk_size = 4096  # 4KB chunks
                
                while True:
                    data = sock.recv(chunk_size)
                    if not data:
                        break
                    
                    f.write(data)
                    total_bytes += len(data)
                    
                    # Show progress
                    if total_bytes % (chunk_size * 100) == 0:  # Every ~400KB
                        print(f"Received: {total_bytes / 1024:.1f} KB", end='\r')
                
                print(f"\nStream completed! Total received: {total_bytes / 1024:.1f} KB")
                print(f"Video saved as: {output_file}")
                
    except ConnectionRefusedError:
        print(f"Error: Could not connect to {server_ip}:{server_port}")
        print("Make sure the server is running and the IP address is correct.")
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function with command line argument handling"""
    
    if len(sys.argv) < 2:
        print("Usage: python3 stream_client.py <server_ip> [output_file.h264]")
        print("Example: python3 stream_client.py 192.168.1.100")
        print("Example: python3 stream_client.py 192.168.1.100 my_video.h264")
        sys.exit(1)
    
    server_ip = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Validate IP address format (basic check)
    try:
        socket.inet_aton(server_ip)
    except socket.error:
        print(f"Error: '{server_ip}' is not a valid IP address")
        sys.exit(1)
    
    connect_and_receive_stream(server_ip, output_file=output_file)
    
    # Provide playback instructions
    if os.path.exists(output_file or f"received_stream_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h264"):
        print("\nTo play the video, you can use:")
        print(f"  vlc {output_file or 'received_stream_*.h264'}")
        print(f"  ffplay {output_file or 'received_stream_*.h264'}")
        print(f"  mpv {output_file or 'received_stream_*.h264'}")

if __name__ == "__main__":
    main()