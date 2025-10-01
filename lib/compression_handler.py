#!/usr/bin/python3
"""
Compression Handler for Raspberry Pi Camera Streaming
Optimized for ESP32 integration with multiple compression formats
"""

import cv2
import numpy as np
import time
from typing import Optional, Dict, Any
from enum import Enum


class CompressionFormat(Enum):
    """Supported compression formats"""

    JPEG = "jpeg"
    WEBP = "webp"
    PNG = "png"
    BMP = "bmp"


class CompressionHandler:
    """
    Handles image compression with various formats and quality settings
    Optimized for ESP32 streaming and memory efficiency
    """

    def __init__(self, default_format=CompressionFormat.JPEG, default_quality=85):
        """
        Initialize compression handler

        Args:
            default_format: Default compression format
            default_quality: Default quality setting (1-100 for JPEG/WEBP)
        """
        self.default_format = default_format
        self.default_quality = default_quality
        self.stats = {
            "total_compressions": 0,
            "total_bytes_in": 0,
            "total_bytes_out": 0,
            "avg_compression_ratio": 0.0,
            "avg_processing_time": 0.0,
            "format_usage": {},
        }

        # Check format support
        self.supported_formats = self._check_format_support()
        print(f"CompressionHandler initialized with format: {default_format.value}")
        print(f"Supported formats: {list(self.supported_formats.keys())}")

    def _check_format_support(self) -> Dict[str, bool]:
        """Check which compression formats are supported by OpenCV"""
        test_image = np.zeros((10, 10, 3), dtype=np.uint8)
        supported = {}

        # Test JPEG
        try:
            success, _ = cv2.imencode(".jpg", test_image)
            supported["jpeg"] = success
        except Exception:
            supported["jpeg"] = False

        # Test PNG
        try:
            success, _ = cv2.imencode(".png", test_image)
            supported["png"] = success
        except Exception:
            supported["png"] = False

        # Test WEBP
        try:
            success, _ = cv2.imencode(".webp", test_image)
            supported["webp"] = success
        except Exception:
            supported["webp"] = False

        # Test BMP
        try:
            success, _ = cv2.imencode(".bmp", test_image)
            supported["bmp"] = success
        except Exception:
            supported["bmp"] = False

        return supported

    def compress_image(
        self,
        frame: np.ndarray,
        format_type: Optional[CompressionFormat] = None,
        quality: Optional[int] = None,
        custom_params: Optional[Dict] = None,
    ) -> Optional[bytes]:
        """
        Compress image with specified format and quality

        Args:
            frame: Input image frame
            format_type: Compression format (uses default if None)
            quality: Quality setting (uses default if None)
            custom_params: Custom compression parameters

        Returns:
            Compressed image bytes or None if compression fails
        """
        start_time = time.time()

        # Use defaults if not specified
        if format_type is None:
            format_type = self.default_format
        if quality is None:
            quality = self.default_quality

        # Check format support
        if not self.supported_formats.get(format_type.value, False):
            print(f"Format {format_type.value} not supported")
            return None

        try:
            # Get compression parameters
            params = self._get_compression_params(format_type, quality, custom_params)

            # Get file extension
            ext = self._get_file_extension(format_type)

            # Compress image
            success, compressed_buffer = cv2.imencode(ext, frame, params)

            if success:
                compressed_bytes = compressed_buffer.tobytes()

                # Update statistics
                self._update_stats(
                    frame, compressed_bytes, format_type, time.time() - start_time
                )

                return compressed_bytes
            else:
                print(f"Compression failed for format {format_type.value}")
                return None

        except Exception as e:
            print(f"Compression error: {e}")
            return None

    def _get_compression_params(
        self,
        format_type: CompressionFormat,
        quality: int,
        custom_params: Optional[Dict],
    ) -> list:
        """Get compression parameters for OpenCV"""
        params = []

        if format_type == CompressionFormat.JPEG:
            params.extend([cv2.IMWRITE_JPEG_QUALITY, quality])
            # ESP32 optimization: progressive JPEG can be slower to decode
            params.extend([cv2.IMWRITE_JPEG_PROGRESSIVE, 0])
            params.extend([cv2.IMWRITE_JPEG_OPTIMIZE, 1])

        elif format_type == CompressionFormat.WEBP:
            params.extend([cv2.IMWRITE_WEBP_QUALITY, quality])

        elif format_type == CompressionFormat.PNG:
            # PNG compression level (0-9, higher = smaller file but slower)
            compression_level = min(9, max(0, int((100 - quality) / 11)))
            params.extend([cv2.IMWRITE_PNG_COMPRESSION, compression_level])

        # Add custom parameters
        if custom_params:
            for key, value in custom_params.items():
                params.extend([key, value])

        return params

    def _get_file_extension(self, format_type: CompressionFormat) -> str:
        """Get file extension for format"""
        extensions = {
            CompressionFormat.JPEG: ".jpg",
            CompressionFormat.WEBP: ".webp",
            CompressionFormat.PNG: ".png",
            CompressionFormat.BMP: ".bmp",
        }
        return extensions[format_type]

    def compress_for_esp32(
        self, frame: np.ndarray, target_size_kb: int = 10
    ) -> Optional[bytes]:
        """
        Compress image optimized for ESP32 with target file size

        Args:
            frame: Input frame
            target_size_kb: Target size in kilobytes

        Returns:
            Compressed bytes that fit target size
        """
        target_size_bytes = target_size_kb * 1024

        # Start with good quality and reduce if needed
        for quality in [85, 75, 65, 55, 45, 35, 25]:
            compressed = self.compress_image(frame, CompressionFormat.JPEG, quality)

            if compressed and len(compressed) <= target_size_bytes:
                print(
                    f"ESP32 compression: {len(compressed)} bytes at quality {quality}"
                )
                return compressed

        # If still too large, try reducing resolution
        height, width = frame.shape[:2]
        for scale in [0.8, 0.6, 0.4]:
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized_frame = cv2.resize(frame, (new_width, new_height))

            compressed = self.compress_image(resized_frame, CompressionFormat.JPEG, 25)

            if compressed and len(compressed) <= target_size_bytes:
                print(f"ESP32 compression: {len(compressed)} bytes at scale {scale}")
                return compressed

        print(f"Warning: Could not achieve target size of {target_size_kb}KB")
        # Return best effort compression
        return self.compress_image(frame, CompressionFormat.JPEG, 25)

    def adaptive_quality_compress(
        self,
        frame: np.ndarray,
        target_size_kb: int = 15,
        format_type: CompressionFormat = CompressionFormat.JPEG,
    ) -> Optional[bytes]:
        """
        Adaptive compression that finds optimal quality for target size

        Args:
            frame: Input frame
            target_size_kb: Target size in kilobytes
            format_type: Compression format

        Returns:
            Optimally compressed bytes
        """
        target_size = target_size_kb * 1024

        # Binary search for optimal quality
        low_quality, high_quality = 10, 95
        best_compression = None
        best_quality = low_quality

        for _ in range(7):  # Max 7 iterations for binary search
            mid_quality = (low_quality + high_quality) // 2
            compressed = self.compress_image(frame, format_type, mid_quality)

            if not compressed:
                high_quality = mid_quality - 1
                continue

            if len(compressed) <= target_size:
                best_compression = compressed
                best_quality = mid_quality
                low_quality = mid_quality + 1
            else:
                high_quality = mid_quality - 1

        if best_compression:
            print(
                f"Adaptive compression: {len(best_compression)} bytes at quality {best_quality}"
            )

        return best_compression

    def benchmark_formats(self, test_frame: np.ndarray, qualities: list = None) -> Dict:
        """
        Benchmark different compression formats

        Args:
            test_frame: Frame to use for testing
            qualities: List of qualities to test (default: [50, 75, 90])

        Returns:
            Benchmark results dictionary
        """
        if qualities is None:
            qualities = [50, 75, 90]

        results = {}
        original_size = test_frame.nbytes

        for format_type in [
            CompressionFormat.JPEG,
            CompressionFormat.WEBP,
            CompressionFormat.PNG,
        ]:
            if not self.supported_formats.get(format_type.value, False):
                continue

            format_results = {}

            for quality in qualities:
                start_time = time.time()
                compressed = self.compress_image(test_frame, format_type, quality)
                end_time = time.time()

                if compressed:
                    format_results[f"quality_{quality}"] = {
                        "size_bytes": len(compressed),
                        "compression_ratio": len(compressed) / original_size,
                        "size_reduction_percent": (1 - len(compressed) / original_size)
                        * 100,
                        "compression_time_ms": (end_time - start_time) * 1000,
                    }

            results[format_type.value] = format_results

        return results

    def create_thumbnail(
        self, frame: np.ndarray, max_size: tuple = (160, 120), quality: int = 75
    ) -> Optional[bytes]:
        """
        Create compressed thumbnail for preview

        Args:
            frame: Input frame
            max_size: Maximum thumbnail dimensions (width, height)
            quality: Compression quality

        Returns:
            Compressed thumbnail bytes
        """
        # Calculate thumbnail size maintaining aspect ratio
        height, width = frame.shape[:2]
        max_width, max_height = max_size

        # Calculate scaling factor
        scale_w = max_width / width
        scale_h = max_height / height
        scale = min(scale_w, scale_h)

        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            thumbnail = cv2.resize(
                frame, (new_width, new_height), interpolation=cv2.INTER_AREA
            )
        else:
            thumbnail = frame

        return self.compress_image(thumbnail, CompressionFormat.JPEG, quality)

    def _update_stats(
        self,
        original_frame: np.ndarray,
        compressed_bytes: bytes,
        format_type: CompressionFormat,
        processing_time: float,
    ):
        """Update compression statistics"""
        original_size = original_frame.nbytes
        compressed_size = len(compressed_bytes)
        compression_ratio = compressed_size / original_size

        self.stats["total_compressions"] += 1
        self.stats["total_bytes_in"] += original_size
        self.stats["total_bytes_out"] += compressed_size

        # Update averages
        if self.stats["avg_compression_ratio"] == 0:
            self.stats["avg_compression_ratio"] = compression_ratio
        else:
            self.stats["avg_compression_ratio"] = (
                self.stats["avg_compression_ratio"] * 0.9 + compression_ratio * 0.1
            )

        processing_time_ms = processing_time * 1000
        if self.stats["avg_processing_time"] == 0:
            self.stats["avg_processing_time"] = processing_time_ms
        else:
            self.stats["avg_processing_time"] = (
                self.stats["avg_processing_time"] * 0.9 + processing_time_ms * 0.1
            )

        # Format usage
        format_name = format_type.value
        if format_name not in self.stats["format_usage"]:
            self.stats["format_usage"][format_name] = 0
        self.stats["format_usage"][format_name] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        stats = self.stats.copy()
        if stats["total_bytes_in"] > 0:
            stats["overall_compression_ratio"] = (
                stats["total_bytes_out"] / stats["total_bytes_in"]
            )
            stats["overall_size_reduction_percent"] = (
                1 - stats["overall_compression_ratio"]
            ) * 100
        else:
            stats["overall_compression_ratio"] = 0
            stats["overall_size_reduction_percent"] = 0

        return stats

    def reset_stats(self):
        """Reset compression statistics"""
        self.stats = {
            "total_compressions": 0,
            "total_bytes_in": 0,
            "total_bytes_out": 0,
            "avg_compression_ratio": 0.0,
            "avg_processing_time": 0.0,
            "format_usage": {},
        }


# Helper functions for easy integration
def create_compression_handler(esp32_optimized: bool = True) -> CompressionHandler:
    """
    Create compression handler with optimal settings

    Args:
        esp32_optimized: If True, use ESP32-optimized settings

    Returns:
        Configured CompressionHandler instance
    """
    if esp32_optimized:
        # JPEG with good quality/size balance for ESP32
        return CompressionHandler(CompressionFormat.JPEG, quality=75)
    else:
        # Higher quality for general use
        return CompressionHandler(CompressionFormat.JPEG, quality=90)


def quick_jpeg_compress(frame: np.ndarray, quality: int = 85) -> Optional[bytes]:
    """
    Quick JPEG compression without creating handler instance

    Args:
        frame: Input frame
        quality: JPEG quality (1-100)

    Returns:
        Compressed JPEG bytes
    """
    try:
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        success, jpeg_buffer = cv2.imencode(".jpg", frame, encode_params)

        if success:
            return jpeg_buffer.tobytes()
        else:
            return None
    except Exception as e:
        print(f"Quick JPEG compression error: {e}")
        return None


def test_compression_handler():
    """Test function for compression handler"""
    print("Testing compression handler...")

    try:
        # Test with camera if available
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Camera not available for testing")
            return False

        # Create handler
        handler = create_compression_handler(esp32_optimized=True)

        print("Press 'q' to quit, 'b' to benchmark, 't' for thumbnail test")
        print("Press '1-4' to change format: 1=JPEG, 2=WEBP, 3=PNG, 4=BMP")

        formats = [
            CompressionFormat.JPEG,
            CompressionFormat.WEBP,
            CompressionFormat.PNG,
            CompressionFormat.BMP,
        ]
        current_format = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Compress frame
            compressed_data = handler.compress_image(frame, formats[current_format])

            # Show original and info
            info_text = f"Format: {formats[current_format].value.upper()}"
            cv2.putText(
                frame,
                info_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            if compressed_data:
                size_kb = len(compressed_data) / 1024
                size_text = f"Size: {size_kb:.1f} KB"
                cv2.putText(
                    frame,
                    size_text,
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )

            stats = handler.get_stats()
            stats_text = f"Compressions: {stats['total_compressions']}, Avg: {stats['avg_processing_time']:.1f}ms"
            cv2.putText(
                frame,
                stats_text,
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

            cv2.imshow("Compression Test", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("b"):
                print("Running benchmark...")
                results = handler.benchmark_formats(frame)
                print("Benchmark results:")
                for format_name, format_results in results.items():
                    print(f"  {format_name.upper()}:")
                    for quality, result in format_results.items():
                        print(
                            f"    {quality}: {result['size_bytes']} bytes "
                            f"({result['size_reduction_percent']:.1f}% reduction, "
                            f"{result['compression_time_ms']:.1f}ms)"
                        )
            elif key == ord("t"):
                print("Testing thumbnail creation...")
                thumbnail_data = handler.create_thumbnail(frame)
                if thumbnail_data:
                    print(f"Thumbnail size: {len(thumbnail_data)} bytes")
            elif key in [ord("1"), ord("2"), ord("3"), ord("4")]:
                format_idx = int(chr(key)) - 1
                if format_idx < len(formats):
                    current_format = format_idx
                    print(f"Switched to format: {formats[current_format].value}")

        cap.release()
        cv2.destroyAllWindows()

        # Final stats
        final_stats = handler.get_stats()
        print(f"Final stats: {final_stats}")

        return True

    except Exception as e:
        print(f"Test error: {e}")
        return False


if __name__ == "__main__":
    test_compression_handler()
