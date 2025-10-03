#!/usr/bin/python3
"""
Optimized Grayscale Handler for Raspberry Pi Camera Streaming
Simplified for ESP32 integration
"""

import cv2
import numpy as np
from typing import Optional


class GrayscaleHandler:
    """
    Simple, optimized grayscale conversion handler
    Uses OpenCV's optimized BGR2GRAY conversion for best performance
    """

    def __init__(self):
        """Initialize grayscale handler"""
        print("GrayscaleHandler initialized with OpenCV BGR2GRAY")

    def get_grayscale_jpeg(
        self, frame: np.ndarray, quality: int = 85
    ) -> Optional[bytes]:
        """
        Convert frame to grayscale and encode as JPEG

        Args:
            frame: Input BGR frame
            quality: JPEG quality (1-100)

        Returns:
            JPEG encoded bytes or None if encoding fails
        """
        try:
            # Convert to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Convert back to 3-channel for JPEG encoding
            gray_3ch = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

            # Encode as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            success, jpeg_buffer = cv2.imencode(".jpg", gray_3ch, encode_params)

            if success:
                return jpeg_buffer.tobytes()
            else:
                return None

        except Exception as e:
            print(f"JPEG encoding error: {e}")
            return None


# Helper function for easy integration
def create_grayscale_handler(esp32_optimized: bool = True) -> GrayscaleHandler:
    """
    Create a grayscale handler

    Returns:
        Configured GrayscaleHandler instance
    """
    return GrayscaleHandler()
