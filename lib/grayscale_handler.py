#!/usr/bin/python3
"""
Optimized Grayscale Handler for Raspberry Pi Camera Streaming
Simplified single-method approach for ESP32 integration
"""

import cv2
import numpy as np
import time
from typing import Optional


class GrayscaleHandler:
    """
    Simple, optimized grayscale conversion handler
    Uses OpenCV's optimized BGR2GRAY conversion for best performance
    """

    def __init__(self, enable_caching: bool = True):
        """
        Initialize grayscale handler with optimal settings

        Args:
            enable_caching: Enable frame caching for identical frames
        """
        self.enable_caching = enable_caching
        self.cache = {}
        self.stats = {
            "total_conversions": 0,
            "cache_hits": 0,
            "avg_processing_time": 0.0,
        }

        print("GrayscaleHandler initialized with OpenCV BGR2GRAY (optimal method)")

    def convert_to_grayscale(
        self, frame: np.ndarray, return_3channel: bool = False
    ) -> np.ndarray:
        """
        Convert BGR/RGB frame to grayscale using OpenCV's optimized method

        Args:
            frame: Input image frame (BGR or RGB format)
            return_3channel: If True, return 3-channel grayscale for JPEG encoding

        Returns:
            Grayscale frame as numpy array (1 or 3 channels)
        """
        start_time = time.time()

        # Check cache if enabled
        cache_key = None
        if self.enable_caching:
            cache_key = hash(frame.tobytes()) + (1 if return_3channel else 0)
            if cache_key in self.cache:
                self.stats["cache_hits"] += 1
                return self.cache[cache_key]

        # Convert to grayscale using OpenCV's optimized method
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Convert back to 3-channel if needed (for JPEG encoding)
        if return_3channel:
            gray_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

        # Cache result if enabled
        if self.enable_caching and cache_key is not None:
            self.cache[cache_key] = gray_frame
            # Limit cache size to prevent memory issues
            if len(self.cache) > 50:
                # Remove oldest entry
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]

        # Update stats
        processing_time = (time.time() - start_time) * 1000
        self.stats["total_conversions"] += 1

        if self.stats["avg_processing_time"] == 0:
            self.stats["avg_processing_time"] = processing_time
        else:
            self.stats["avg_processing_time"] = (
                self.stats["avg_processing_time"] * 0.8 + processing_time * 0.2
            )

        return gray_frame

    def get_grayscale_jpeg(
        self, frame: np.ndarray, quality: int = 85
    ) -> Optional[bytes]:
        """
        Convert frame to grayscale and encode as JPEG

        Args:
            frame: Input frame
            quality: JPEG quality (1-100)

        Returns:
            JPEG encoded bytes or None if encoding fails
        """
        try:
            # Get 3-channel grayscale for JPEG encoding
            gray_frame = self.convert_to_grayscale(frame, return_3channel=True)

            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            success, jpeg_buffer = cv2.imencode(".jpg", gray_frame, encode_params)

            if success:
                return jpeg_buffer.tobytes()
            else:
                return None

        except Exception as e:
            print(f"JPEG encoding error: {e}")
            return None

    def clear_cache(self):
        """Clear conversion cache"""
        self.cache.clear()
        self.stats["cache_hits"] = 0

    def get_stats(self) -> dict:
        """Get conversion statistics"""
        stats = self.stats.copy()
        stats["cache_size"] = len(self.cache)
        stats["cache_hit_rate"] = (
            self.stats["cache_hits"] / max(1, self.stats["total_conversions"]) * 100
        )
        return stats

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            "total_conversions": 0,
            "cache_hits": 0,
            "avg_processing_time": 0.0,
        }


# Helper functions for easy integration
def create_grayscale_handler(esp32_optimized: bool = True) -> GrayscaleHandler:
    """
    Create a grayscale handler with optimal settings

    Args:
        esp32_optimized: If True, use caching (recommended for ESP32)

    Returns:
        Configured GrayscaleHandler instance
    """
    return GrayscaleHandler(enable_caching=esp32_optimized)


def quick_grayscale(frame: np.ndarray, return_3channel: bool = False) -> np.ndarray:
    """
    Quick grayscale conversion without creating handler instance

    Args:
        frame: Input frame
        return_3channel: If True, return 3-channel grayscale

    Returns:
        Grayscale frame
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if return_3channel:
        gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return gray
