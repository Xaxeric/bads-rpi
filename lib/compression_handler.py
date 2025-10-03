#!/usr/bin/python3
"""
Compression Handler for Raspberry Pi Camera Streaming
Simplified for ESP32 integration - JPEG only
"""

import cv2
import numpy as np
from typing import Optional


class CompressionHandler:
    """
    Simple JPEG compression handler optimized for ESP32 streaming
    """

    def __init__(self, default_quality=85):
        """
        Initialize compression handler

        Args:
            default_quality: Default JPEG quality setting (1-100)
        """
        self.default_quality = default_quality
        print(f"CompressionHandler initialized with JPEG quality: {default_quality}")

    def compress_image(
        self,
        frame: np.ndarray,
        quality: Optional[int] = None,
    ) -> Optional[bytes]:
        """
        Compress image as JPEG with specified quality

        Args:
            frame: Input image frame
            quality: JPEG quality setting (uses default if None)

        Returns:
            Compressed JPEG bytes or None if compression fails
        """
        # Use default quality if not specified
        if quality is None:
            quality = self.default_quality

        try:
            # JPEG compression parameters optimized for ESP32
            params = [
                cv2.IMWRITE_JPEG_QUALITY, quality,
                cv2.IMWRITE_JPEG_PROGRESSIVE, 0,  # Non-progressive for faster ESP32 decode
                cv2.IMWRITE_JPEG_OPTIMIZE, 1      # Optimize for smaller file size
            ]

            # Compress image
            success, compressed_buffer = cv2.imencode(".jpg", frame, params)

            if success:
                return compressed_buffer.tobytes()
            else:
                print("JPEG compression failed")
                return None

        except Exception as e:
            print(f"Compression error: {e}")
            return None


# Helper function for easy integration
def create_compression_handler(esp32_optimized: bool = True) -> CompressionHandler:
    """
    Create compression handler with optimal settings

    Args:
        esp32_optimized: If True, use ESP32-optimized quality (75), else higher quality (90)

    Returns:
        Configured CompressionHandler instance
    """
    if esp32_optimized:
        return CompressionHandler(default_quality=75)
    else:
        return CompressionHandler(default_quality=90)
