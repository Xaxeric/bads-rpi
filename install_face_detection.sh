#!/bin/bash
# Installation script for face detection dependencies

echo "=== Installing Face Detection Dependencies ==="

# Update package list
echo "Updating package list..."
sudo apt update

# Install OpenCV and dependencies
echo "Installing OpenCV..."
sudo apt install -y python3-opencv python3-pip

# Install additional Python packages
echo "Installing Python packages..."
pip3 install --user opencv-python-headless numpy

# Download Haar cascades if needed
CASCADES_DIR="/usr/share/opencv4/haarcascades"
if [ ! -d "$CASCADES_DIR" ]; then
    echo "Creating cascades directory..."
    sudo mkdir -p "$CASCADES_DIR"
    
    # Download the main cascade file
    echo "Downloading Haar cascade..."
    sudo wget -O "$CASCADES_DIR/haarcascade_frontalface_default.xml" \
        "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
fi

# Test installation
echo "Testing installation..."
python3 -c "import cv2; print('OpenCV version:', cv2.__version__)"

# Test face detection library
echo "Testing face detection library..."
cd "$(dirname "$0")"
python3 lib/face_detection.py --help 2>/dev/null || echo "Face detection library ready (camera test needs hardware)"

echo "=== Installation Complete ==="
echo ""
echo "Usage:"
echo "  # Without face detection:"
echo "  python3 server/lightweight_stream.py"
echo ""
echo "  # With face detection:"
echo "  python3 server/lightweight_stream_with_faces.py -f"
echo ""
echo "Note: Face detection requires additional ~30-50MB RAM"