#!/usr/bin/python3

import requests
import sys
from io import BytesIO
from PIL import Image
import numpy as np


def create_test_image():
    """Create a simple test image"""
    # Create a 640x480 test image with colored rectangles
    img_array = np.zeros((480, 640, 3), dtype=np.uint8)

    # Add colored rectangles
    img_array[50:150, 50:150] = [255, 0, 0]  # Red square
    img_array[50:150, 200:300] = [0, 255, 0]  # Green square
    img_array[50:150, 350:450] = [0, 0, 255]  # Blue square

    # Add timestamp text area (white background)
    img_array[400:450, 50:590] = [255, 255, 255]

    # Convert to PIL Image
    img = Image.fromarray(img_array)

    # Save to bytes buffer
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)

    return buffer


def test_api_endpoint(api_url):
    """Test the API endpoint with a sample image"""
    print(f"Testing API endpoint: {api_url}")

    try:
        # Create test image
        print("Creating test image...")
        image_buffer = create_test_image()

        # Prepare form data
        files = {"image": ("test_image.jpg", image_buffer.getvalue(), "image/jpeg")}

        # Send request
        print("Sending POST request...")
        response = requests.post(api_url, files=files, timeout=10)

        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")

        if response.status_code == 200:
            print("✓ API test successful!")
            return True
        else:
            print("✗ API test failed!")
            return False

    except requests.exceptions.ConnectionError:
        print("✗ Connection error - API server might be down")
        return False
    except requests.exceptions.Timeout:
        print("✗ Request timeout")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        if "image_buffer" in locals():
            image_buffer.close()


def main():
    api_url = "http://192.168.18.11:3000/api/capture"

    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Usage: python3 test_api.py [api_url]")
            print(f"Default URL: {api_url}")
            sys.exit(0)
        api_url = sys.argv[1]

    print("=== API Endpoint Tester ===")
    test_api_endpoint(api_url)


if __name__ == "__main__":
    main()
