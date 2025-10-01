#!/usr/bin/python3
"""
Configuration module for Flask Camera Server
Centralizes all configuration settings
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CameraConfig:
    """Camera configuration settings"""
    width: int = 320
    height: int = 240
    format: str = "RGB888"
    buffer_count: int = 2
    warmup_time: float = 1.0


@dataclass
class CompressionConfig:
    """Compression configuration settings"""
    default_quality: int = 85
    grayscale_quality: int = 80
    esp32_target_size_kb: int = 8
    compressed_quality: int = 50


@dataclass
class StreamConfig:
    """Streaming configuration settings"""
    fps_delay: float = 0.1  # ~10 FPS
    compressed_fps_delay: float = 0.15  # ~6-7 FPS
    error_retry_delay: float = 0.1


@dataclass
class FaceDetectionConfig:
    """Face detection configuration settings"""
    detection_interval: float = 2.0
    lightweight_mode: bool = True


@dataclass
class ServerConfig:
    """Main server configuration"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    threaded: bool = True
    
    # Feature flags
    face_detection_enabled: bool = False
    grayscale_enabled: bool = False
    compression_enabled: bool = False
    
    # Sub-configurations
    camera: CameraConfig = None
    compression: CompressionConfig = None
    streaming: StreamConfig = None
    face_detection: FaceDetectionConfig = None
    
    def __post_init__(self):
        if self.camera is None:
            self.camera = CameraConfig()
        if self.compression is None:
            self.compression = CompressionConfig()
        if self.streaming is None:
            self.streaming = StreamConfig()
        if self.face_detection is None:
            self.face_detection = FaceDetectionConfig()


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self):
        self.config = ServerConfig()
    
    def update_from_args(self, args_dict: Dict[str, Any]):
        """Update configuration from command line arguments"""
        if 'port' in args_dict:
            self.config.port = args_dict['port']
        
        if 'face_detection' in args_dict:
            self.config.face_detection_enabled = args_dict['face_detection']
        
        if 'grayscale_processing' in args_dict:
            self.config.grayscale_enabled = args_dict['grayscale_processing']
        
        if 'advanced_compression' in args_dict:
            self.config.compression_enabled = args_dict['advanced_compression']
    
    def get_config(self) -> ServerConfig:
        """Get current configuration"""
        return self.config
    
    def get_endpoint_info(self) -> Dict[str, str]:
        """Get endpoint information for display"""
        base_url = f"http://0.0.0.0:{self.config.port}"
        
        return {
            "frame_endpoints": {
                "single_frame": f"{base_url}/frame",
                "grayscale_frame": f"{base_url}/frame_gray",
                "compressed_frame": f"{base_url}/frame_compressed",
            },
            "stream_endpoints": {
                "mjpeg_stream": f"{base_url}/stream",
                "mjpeg_stream_gray": f"{base_url}/stream_gray",
                "mjpeg_stream_compressed": f"{base_url}/stream_compressed",
            },
            "info_endpoints": {
                "server_info": f"{base_url}/info",
                "health_check": f"{base_url}/health",
                "feature_status": f"{base_url}/features",
            }
        }


# Global configuration manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager (Singleton pattern)"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager