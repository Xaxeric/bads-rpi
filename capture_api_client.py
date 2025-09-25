#!/usr/bin/python3

import time
import requests
from datetime import datetime
from io import BytesIO

from picamera2 import Picamera2

class ImageCaptureClient:
    def __init__(self, api_url="http://192.168.18.11:3000/api/capture", capture_interval=0.5):
        self.api_url = api_url
        self.capture_interval = capture_interval  # 500ms = 0.5 seconds
        self.running = False
        self.picam2 = None
        self.capture_count = 0
        
    def setup_camera(self):
        """Initialize and configure the camera"""
        print("Setting up camera...")
        self.picam2 = Picamera2()
        
        # Configure for still image capture
        config = self.picam2.create_still_configuration(
            main={"size": (1280, 720)},  # 720p resolution
            buffer_count=2  # Use double buffering for better performance
        )
        self.picam2.configure(config)
        self.picam2.start()
        
        # Allow camera to warm up
        time.sleep(2)
        print("Camera ready!")
        
    def capture_and_send_image(self):
        """Capture an image and send it to the API server"""
        try:
            # Capture image to memory buffer
            buffer = BytesIO()
            self.picam2.capture_file(buffer, format='jpeg')
            buffer.seek(0)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_at_%H.%M.%S")
            filename = f"camera_image_{timestamp}.jpg"
            
            # Prepare multipart form data
            files = {
                'image': (filename, buffer.getvalue(), 'image/jpeg')
            }
            
            # Send POST request to API
            response = requests.post(
                self.api_url, 
                files=files,
                timeout=5  # 5 second timeout
            )
            
            self.capture_count += 1
            
            if response.status_code == 200:
                print(f"✓ Image {self.capture_count} sent successfully ({filename})")
                return True
            else:
                print(f"✗ Failed to send image {self.capture_count}: HTTP {response.status_code}")
                print(f"  Response: {response.text[:100]}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"✗ Timeout sending image {self.capture_count}")
            return False
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection error sending image {self.capture_count}")
            return False
        except Exception as e:
            print(f"✗ Error capturing/sending image {self.capture_count}: {e}")
            return False
        finally:
            buffer.close()
    
    def capture_loop(self):
        """Main capture loop - runs every 500ms"""
        print(f"Starting capture loop (every {self.capture_interval}s)")
        print(f"Sending images to: {self.api_url}")
        print("Press Ctrl+C to stop\n")
        
        last_capture_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check if it's time for next capture
                if current_time - last_capture_time >= self.capture_interval:
                    self.capture_and_send_image()
                    last_capture_time = current_time
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.01)  # 10ms sleep
                
            except KeyboardInterrupt:
                print("\nStopping capture...")
                break
            except Exception as e:
                print(f"Error in capture loop: {e}")
                time.sleep(1)  # Wait before retrying
    
    def start_capture(self, duration=None):
        """Start the image capture process"""
        try:
            self.setup_camera()
            self.running = True
            
            if duration:
                print(f"Capturing for {duration} seconds...")
                # Run for specified duration
                end_time = time.time() + duration
                while self.running and time.time() < end_time:
                    self.capture_loop()
            else:
                # Run indefinitely
                self.capture_loop()
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.picam2:
            print("Stopping camera...")
            self.picam2.stop()
            self.picam2.close()
        
        print(f"\nTotal images captured: {self.capture_count}")

def main():
    """Main function"""
    import sys
    
    # Default settings
    api_url = "http://192.168.18.11:3000/api/capture"
    interval = 0.5  # 500ms
    duration = None  # Run indefinitely
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("Usage: python3 capture_api_client.py [api_url] [interval] [duration]")
            print("  api_url:  REST API endpoint (default: http://192.168.18.11:3000/api/capture)")
            print("  interval: Capture interval in seconds (default: 0.5)")
            print("  duration: Run duration in seconds (default: unlimited)")
            print("\nExamples:")
            print("  python3 capture_api_client.py")
            print("  python3 capture_api_client.py http://localhost:3000/api/capture")
            print("  python3 capture_api_client.py http://localhost:3000/api/capture 1.0")
            print("  python3 capture_api_client.py http://localhost:3000/api/capture 0.5 30")
            sys.exit(0)
        
        api_url = sys.argv[1]
        
        if len(sys.argv) > 2:
            try:
                interval = float(sys.argv[2])
            except ValueError:
                print(f"Error: Invalid interval '{sys.argv[2]}'. Must be a number.")
                sys.exit(1)
        
        if len(sys.argv) > 3:
            try:
                duration = float(sys.argv[3])
            except ValueError:
                print(f"Error: Invalid duration '{sys.argv[3]}'. Must be a number.")
                sys.exit(1)
    
    print("=== Image Capture API Client ===")
    print(f"API URL: {api_url}")
    print(f"Capture Interval: {interval}s ({int(1/interval)} fps)")
    if duration:
        print(f"Duration: {duration}s")
    else:
        print("Duration: Unlimited (Ctrl+C to stop)")
    print()
    
    # Test API connectivity first
    try:
        print("Testing API connectivity...")
        response = requests.get(api_url.replace('/capture', '/'), timeout=5)
        print(f"API server responded: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not reach API server ({e})")
        print("Continuing anyway - will show errors during capture if API is down")
    
    print()
    
    # Create and start the capture client
    client = ImageCaptureClient(api_url, interval)
    client.start_capture(duration)

if __name__ == "__main__":
    main()