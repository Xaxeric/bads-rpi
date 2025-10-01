"""
Core package for Flask Camera Server
Contains the main camera server logic
"""

from .camera_server import CameraServer, get_camera_server

__all__ = ['CameraServer', 'get_camera_server']