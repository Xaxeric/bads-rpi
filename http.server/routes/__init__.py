"""
Routes package for Flask Camera Server
Each route is separated into its own module for better organization
"""

from .frame_routes import frame_bp
from .stream_routes import stream_bp
from .info_routes import info_bp

__all__ = ['frame_bp', 'stream_bp', 'info_bp']