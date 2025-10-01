# Modular Flask Camera Server

This is a refactored version of the Flask camera server following SOLID principles and modular design.

## Directory Structure

```
http_server/
├── app.py                  # Main application entry point
├── core/                   # Core functionality modules
│   ├── __init__.py
│   ├── camera_server.py    # Camera server core logic
│   └── config.py          # Configuration management
└── routes/                 # Route modules (separated by functionality)
    ├── __init__.py
    ├── frame_routes.py     # Single frame capture endpoints
    ├── stream_routes.py    # MJPEG streaming endpoints
    └── info_routes.py      # Server info and status endpoints
```

## Design Principles Applied

### 1. Single Responsibility Principle (SRP)
- **CameraServer**: Only handles camera operations and frame processing
- **Frame Routes**: Only handles single frame requests
- **Stream Routes**: Only handles streaming functionality
- **Info Routes**: Only handles server information and status

### 2. Open/Closed Principle (OCP)
- New route modules can be added without modifying existing code
- New features can be added through configuration without changing core logic

### 3. Liskov Substitution Principle (LSP)
- All route modules follow the same Blueprint pattern
- Camera server can be easily substituted with different implementations

### 4. Interface Segregation Principle (ISP)
- Routes only depend on the camera server methods they actually use
- Configuration is separated into logical groups

### 5. Dependency Inversion Principle (DIP)
- High-level modules (routes) depend on abstractions (camera server interface)
- Camera server is accessed through a factory function (get_camera_server)

# Modular Flask Camera Server

This is a refactored version of the Flask camera server following SOLID principles and modular design. **All features are enabled by default for optimal ESP32 integration.**

## Directory Structure

```
http_server/
├── app.py                  # Main application entry point
├── core/                   # Core functionality modules
│   ├── __init__.py
│   ├── camera_server.py    # Camera server core logic
│   └── config.py          # Configuration management
└── routes/                 # Route modules (separated by functionality)
    ├── __init__.py
    ├── frame_routes.py     # Single frame capture endpoints
    ├── stream_routes.py    # MJPEG streaming endpoints
    └── info_routes.py      # Server info and status endpoints
```

## Features Enabled by Default

✅ **Face Detection**: Lightweight face detection optimized for Pi  
✅ **Grayscale Processing**: Memory-efficient grayscale conversion  
✅ **Advanced Compression**: ESP32-optimized compression with target file sizes  

## Running the Server

```bash
# Start server with all features enabled (default port 5000)
python app.py

# Start server on custom port
python app.py 8080
```

## Available Endpoints

### Frame Endpoints (Single Capture)
- `GET /frame` - Standard JPEG frame (320x240)
- `GET /frame_gray` - Grayscale JPEG frame (smaller size)
- `GET /frame_compressed` - Highly compressed JPEG frame (ESP32 optimized)

### Stream Endpoints (MJPEG)
- `GET /stream` - Standard MJPEG stream (~10 FPS)
- `GET /stream_gray` - Grayscale MJPEG stream (memory efficient)
- `GET /stream_compressed` - Compressed MJPEG stream (~6-7 FPS, ultra-low bandwidth)

### Info Endpoints
- `GET /` - Basic server information
- `GET /info` - Detailed server status and usage examples
- `GET /health` - Health check endpoint for monitoring
- `GET /features` - Feature availability and status details

## Benefits of This Structure

1. **Maintainability**: Each route is in its own file, making it easy to find and modify
2. **Testability**: Individual route modules can be tested independently
3. **Scalability**: New endpoints can be added without affecting existing ones
4. **Reusability**: Core camera logic can be reused across different route modules
5. **Configuration**: Centralized configuration management
6. **Error Isolation**: Issues in one route module don't affect others

## Adding New Routes

To add a new route module:

1. Create a new file in the `routes/` directory
2. Create a Blueprint and define your routes
3. Import and register the Blueprint in `routes/__init__.py`
4. Import and register in `app.py`

Example:
```python
# routes/new_feature_routes.py
from flask import Blueprint
new_feature_bp = Blueprint('new_feature', __name__)

@new_feature_bp.route("/new_endpoint")
def new_endpoint():
    return "New feature endpoint"
```

## Configuration

The server uses a centralized configuration system in `core/config.py` that allows for:
- Environment-specific settings
- Feature flags
- Easy parameter tuning
- Configuration validation