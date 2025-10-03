# BADS Camera Server - Systemd Service Setup

This directory contains systemd service files to run the BADS Flask Camera Server automatically on your Raspberry Pi Zero 2W.

## Prerequisites

**Important**: The service is configured to run from `/opt/bads-rpi`. 

Before installing the service, move this project to the correct location:

```bash
# If you're currently in a different location, move the project:
sudo mv /path/to/current/bads-rpi /opt/bads-rpi
sudo chown -R pi:pi /opt/bads-rpi
cd /opt/bads-rpi
```

## Installation Options

You can install the service either **system-wide** (runs at boot) or **user-level** (runs when you log in):

### System-wide Installation (Recommended for headless Pi)
- Starts automatically at boot time
- Runs even if no user is logged in
- Requires sudo for installation

### User-level Installation  
- Starts when the pi user logs in
- Stops when the user logs out
- No sudo required for installation

## Quick Setup

### System-wide Installation (Recommended)
1. **Install the service (requires sudo):**
   ```bash
   make install
   ```

2. **Start the camera server:**
   ```bash
   make start
   ```

3. **Check if it's running:**
   ```bash
   make status
   ```

### User-level Installation (No sudo required)
1. **Install the service (user-level):**
   ```bash
   make install-user
   ```

2. **Start the camera server:**
   ```bash
   make start
   ```

3. **Check if it's running:**
   ```bash
   make status
   ```

## Alternative: Complete Setup

For a complete setup from scratch:

**System-wide (move project + install + start):**
```bash
make setup
```

**User-level (move project + install + start):**
```bash
make setup-user
```

## Files Included

- `bads-camera.service` - Systemd service configuration (configured for `/opt/bads-rpi`)
- `Makefile` - Build system for installation and service management
- `install_service.sh` - Legacy bash installation script (deprecated)
- `camera_service.sh` - Legacy service management script (deprecated)
- `move_to_home.sh` - Helper script to move project to correct location
- `SERVICE_README.md` - This file

## Service Management with Make

Use the Makefile for easy management:

```bash
# View all available commands
make help

# Setup and installation
make install          # Install systemd service (system-wide)
make install-user     # Install systemd service (user-level)
make move-project     # Move project to /opt/bads-rpi
make check-deps       # Check Python dependencies
make install-deps     # Install Python dependencies

# Service control (automatically detects user vs system)
make start            # Start the service
make stop             # Stop the service  
make restart          # Restart the service
make status           # Check status
make logs             # View live logs

# Boot/login configuration
make enable           # Enable auto-start (boot/login)
make disable          # Disable auto-start

# Information
make info             # Show server endpoints
make check-location   # Verify project location

# Cleanup
make uninstall        # Remove system-wide service
make uninstall-user   # Remove user-level service
make clean            # Clean temporary files

# Complete setup
make setup            # System-wide setup (move + install + start)
make setup-user       # User-level setup (move + install + start)
```

## Legacy Scripts (Still Available)

You can still use the bash scripts if preferred:

```bash
# Start the service
./camera_service.sh start

# Stop the service  
./camera_service.sh stop

# Restart the service
./camera_service.sh restart

# Check status
./camera_service.sh status

# View live logs
./camera_service.sh logs

# Enable auto-start on boot
./camera_service.sh enable

# Disable auto-start on boot
./camera_service.sh disable

# Show server endpoints
./camera_service.sh info
```

## Recommended: Use Make Commands

The Makefile provides better error checking and cleaner output:

## Manual Service Commands

If you prefer using systemctl directly:

```bash
# Start service
sudo systemctl start bads-camera

# Stop service
sudo systemctl stop bads-camera

# Restart service
sudo systemctl restart bads-camera

# Check status
sudo systemctl status bads-camera

# Enable auto-start on boot
sudo systemctl enable bads-camera

# Disable auto-start
sudo systemctl disable bads-camera

# View logs
sudo journalctl -u bads-camera -f
```

## Service Configuration

The service is configured with:

- **User**: pi (runs as pi user, not root)
- **Working Directory**: `/opt/bads-rpi`
- **Auto-restart**: Yes (restarts if it crashes)
- **Memory Limit**: 256MB (suitable for Pi Zero 2W)
- **Security**: Restricted permissions for safety

### Installation Locations

**System-wide service:**
- Service file: `/etc/systemd/system/bads-camera.service`
- Starts at boot time
- Requires sudo to manage

**User-level service:**
- Service file: `~/.config/systemd/user/bads-camera.service`
- Starts when user logs in
- No sudo required

## Server Endpoints

Once running, the camera server provides:

- **Single Frame**: `http://your-pi-ip:5000/frame` (Perfect for ESP32)
- **MJPEG Stream**: `http://your-pi-ip:5000/stream` (For browsers)
- **Server Info**: `http://your-pi-ip:5000/info`
- **Main Page**: `http://your-pi-ip:5000/`

## Database Integration

The service automatically sends grayscale frames to:
- **Target**: `192.168.18.11:3000/api/capture`
- **Format**: Multipart form-data with JPEG images
- **Frequency**: Every captured frame

## Project Directory Structure

The service expects this structure at `/opt/bads-rpi/`:

```
/opt/bads-rpi/
├── http/
│   └── flask_camera_server.py    # Main server file
├── lib/
│   ├── face_detection.py         # Face detection library
│   ├── grayscale_handler.py      # Grayscale processing
│   └── compression_handler.py    # JPEG compression
├── bads-camera.service           # Systemd service file
├── Makefile                      # Build system
├── install_service.sh            # Legacy installation script
└── camera_service.sh             # Legacy management script
```

## Installation Steps

### Method 1: Using Make (Recommended)

1. **Check available commands:**
   ```bash
   make help
   ```

2. **Complete setup (move + install + start):**
   ```bash
   make setup
   ```

### Method 2: Step-by-step with Make

1. **Move project to correct location:**
   ```bash
   make move-project
   cd /opt/bads-rpi
   ```

2. **Install dependencies (if needed):**
   ```bash
   make install-deps
   ```

3. **Install the service (choose one):**
   ```bash
   make install        # System-wide (requires sudo)
   # OR
   make install-user   # User-level (no sudo)
   ```

4. **Start the service:**
   ```bash
   make start
   ```

### Method 3: Legacy Scripts

1. **Move project to correct location:**
   ```bash
   sudo mv /current/path/bads-rpi /opt/bads-rpi
   sudo chown -R pi:pi /opt/bads-rpi
   cd /opt/bads-rpi
   ```

2. **Make scripts executable:**
   ```bash
   chmod +x install_service.sh camera_service.sh
   ```

3. **Install the service:**
   ```bash
   ./install_service.sh
   ```

4. **Start the service:**
   ```bash
   ./camera_service.sh start
   ```

## Troubleshooting

### Service won't start
```bash
# Check detailed logs
sudo journalctl -u bads-camera -n 50

# Check if dependencies are installed
python3 -c "import cv2, picamera2, flask, requests"

# Verify project is in correct location
ls -la /home/pi/bads-rpi/http/flask_camera_server.py
```

### Permission issues
```bash
# Ensure correct ownership
sudo chown -R pi:pi /home/pi/bads-rpi

# Check service file permissions
ls -la /etc/systemd/system/bads-camera.service
```

### Camera not working
```bash
# Test camera manually
python3 -c "from picamera2 import Picamera2; print('Camera OK')"

# Check if camera is enabled
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
```

### Wrong directory error
If you get "No such file or directory" errors, ensure:
```bash
# Project is in the correct location
ls /home/pi/bads-rpi/http/flask_camera_server.py

# If not, move it:
sudo mv /current/location/bads-rpi /home/pi/bads-rpi
sudo chown -R pi:pi /home/pi/bads-rpi
```

## Performance Optimization for Pi Zero 2W

The service is pre-configured for optimal Pi Zero 2W performance:

- **Face Detection**: Lightweight mode enabled
- **Resolution**: 320x240 (ESP32 compatible)
- **Processing**: Grayscale pipeline for efficiency
- **Memory**: Limited to prevent system overload
- **Detection Interval**: 1.5 seconds for balance

## Uninstalling

To remove the service:

```bash
# Stop and disable
sudo systemctl stop bads-camera
sudo systemctl disable bads-camera

# Remove service file
sudo rm /etc/systemd/system/bads-camera.service

# Reload systemd
sudo systemctl daemon-reload
```

## Auto-Start on Boot

The installation script automatically enables the service to start on boot. This means:

- Camera server starts automatically when Pi boots
- Service restarts if it crashes
- No manual intervention needed

Perfect for headless Raspberry Pi deployments! 🎯