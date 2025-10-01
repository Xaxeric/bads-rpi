#!/usr/bin/python3
"""
Grayscale Handler for Raspberry Pi Camera Streaming
Optimized for ESP32 integration and performance
"""

import cv2
import numpy as np
import time
from typing import Optional


class GrayscaleHandler:
    """
    Handles grayscale conversion with various optimization options
    Designed for ESP32 streaming applications
    """

    def __init__(self, method="cv2_weighted", enable_caching=True):
        """
        Initialize grayscale handler

        Args:
            method: Conversion method ('cv2_weighted', 'cv2_fast', 'numpy_mean', 'numpy_weighted')
            enable_caching: Cache conversion results for identical frames
        """
        self.method = method
        self.enable_caching = enable_caching
        self.cache = {}
        self.stats = {
            "total_conversions": 0,
            "cache_hits": 0,
            "avg_processing_time": 0.0,
        }

        # Validate method
        valid_methods = ["cv2_weighted", "cv2_fast", "numpy_mean", "numpy_weighted"]
        if method not in valid_methods:
            raise ValueError(f"Invalid method. Choose from: {valid_methods}")

        print(f"GrayscaleHandler initialized with method: {method}")

    def convert_to_grayscale(self, frame: np.ndarray) -> np.ndarray:
        """
        Convert BGR/RGB frame to grayscale

        Args:
            frame: Input image frame (BGR or RGB format)

        Returns:
            Grayscale frame as numpy array
        """
        start_time = time.time()

        # Check cache if enabled
        if self.enable_caching:
            frame_hash = hash(frame.tobytes())
            if frame_hash in self.cache:
                self.stats["cache_hits"] += 1
                return self.cache[frame_hash]

        # Convert based on method
        if self.method == "cv2_weighted":
            # OpenCV weighted conversion (most accurate)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        elif self.method == "cv2_fast":
            # OpenCV simple conversion (faster)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        elif self.method == "numpy_mean":
            # Simple mean of RGB channels (fastest)
            gray_frame = np.mean(frame, axis=2).astype(np.uint8)

        elif self.method == "numpy_weighted":
            # Weighted average using luminance formula
            # Y = 0.299*R + 0.587*G + 0.114*B
            weights = np.array([0.114, 0.587, 0.299])  # BGR order
            gray_frame = np.dot(frame, weights).astype(np.uint8)

        # Cache result if enabled
        if self.enable_caching:
            self.cache[frame_hash] = gray_frame
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

    def convert_to_3channel_gray(self, frame: np.ndarray) -> np.ndarray:
        """
        Convert to grayscale but keep 3 channels (for JPEG encoding)

        Args:
            frame: Input BGR/RGB frame

        Returns:
            3-channel grayscale frame
        """
        gray = self.convert_to_grayscale(frame)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    def smart_grayscale(
        self, frame: np.ndarray, quality_threshold: float = 0.7
    ) -> np.ndarray:
        """
        Smart grayscale conversion that maintains some color information
        for better visual quality at the cost of slightly larger file size

        Args:
            frame: Input frame
            quality_threshold: Balance between grayscale and color (0.0 = full gray, 1.0 = full color)

        Returns:
            Processed frame
        """
        if quality_threshold <= 0:
            return self.convert_to_3channel_gray(frame)
        elif quality_threshold >= 1:
            return frame

        # Create weighted blend between grayscale and original
        gray_3ch = self.convert_to_3channel_gray(frame)
        blended = cv2.addWeighted(
            gray_3ch, 1 - quality_threshold, frame, quality_threshold, 0
        )

        return blended

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
            gray_frame = self.convert_to_3channel_gray(frame)

            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            success, jpeg_buffer = cv2.imencode(".jpg", gray_frame, encode_params)

            if success:
                return jpeg_buffer.tobytes()
            else:
                return None

        except Exception as e:
            print(f"JPEG encoding error: {e}")
            return None

    def benchmark_methods(self, test_frame: np.ndarray, iterations: int = 100) -> dict:
        """
        Benchmark different grayscale conversion methods

        Args:
            test_frame: Frame to use for testing
            iterations: Number of test iterations

        Returns:
            Dictionary with benchmark results
        """
        methods = ["cv2_weighted", "cv2_fast", "numpy_mean", "numpy_weighted"]
        results = {}

        for method in methods:
            # Create temporary handler
            temp_handler = GrayscaleHandler(method=method, enable_caching=False)

            start_time = time.time()
            for _ in range(iterations):
                temp_handler.convert_to_grayscale(test_frame.copy())
            end_time = time.time()

            avg_time = ((end_time - start_time) / iterations) * 1000  # ms
            results[method] = {
                "avg_time_ms": avg_time,
                "fps_potential": 1000 / avg_time if avg_time > 0 else float("inf"),
            }

        return results

    def set_method(self, method: str):
        """Change conversion method"""
        valid_methods = ["cv2_weighted", "cv2_fast", "numpy_mean", "numpy_weighted"]
        if method not in valid_methods:
            raise ValueError(f"Invalid method. Choose from: {valid_methods}")

        self.method = method
        self.clear_cache()
        print(f"Grayscale method changed to: {method}")

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
        esp32_optimized: If True, use settings optimized for ESP32 streaming

    Returns:
        Configured GrayscaleHandler instance
    """
    if esp32_optimized:
        # Fast method with caching for ESP32
        return GrayscaleHandler(method="cv2_fast", enable_caching=True)
    else:
        # High quality method
        return GrayscaleHandler(method="cv2_weighted", enable_caching=True)


def quick_grayscale(frame: np.ndarray, method: str = "cv2_fast") -> np.ndarray:
    """
    Quick grayscale conversion without creating handler instance

    Args:
        frame: Input frame
        method: Conversion method

    Returns:
        Grayscale frame
    """
    if method == "cv2_fast" or method == "cv2_weighted":
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    elif method == "numpy_mean":
        return np.mean(frame, axis=2).astype(np.uint8)
    elif method == "numpy_weighted":
        weights = np.array([0.114, 0.587, 0.299])  # BGR order
        return np.dot(frame, weights).astype(np.uint8)
    else:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def test_grayscale_handler():
    """Test function for grayscale handler"""
    print("Testing grayscale handler...")

    try:
        # Test with camera if available
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Camera not available for testing")
            return False

        # Create handler
        handler = create_grayscale_handler(esp32_optimized=True)

        print("Press 'q' to quit, 'm' to cycle methods, 'b' to benchmark")
        methods = ["cv2_weighted", "cv2_fast", "numpy_mean", "numpy_weighted"]
        current_method_idx = 1  # Start with cv2_fast

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert to grayscale
            gray_frame = handler.convert_to_3channel_gray(frame)

            # Create side-by-side comparison
            display_frame = np.hstack([frame, gray_frame])

            # Add info text
            info_text = f"Method: {handler.method}"
            cv2.putText(
                display_frame,
                info_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            stats = handler.get_stats()
            stats_text = f"Conversions: {stats['total_conversions']}, Avg: {stats['avg_processing_time']:.1f}ms"
            cv2.putText(
                display_frame,
                stats_text,
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

            cv2.imshow("Grayscale Test (Original | Grayscale)", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("m"):
                # Cycle through methods
                current_method_idx = (current_method_idx + 1) % len(methods)
                handler.set_method(methods[current_method_idx])
            elif key == ord("b"):
                # Run benchmark
                print("Running benchmark...")
                results = handler.benchmark_methods(frame)
                print("Benchmark results:")
                for method, result in results.items():
                    print(
                        f"  {method}: {result['avg_time_ms']:.2f}ms ({result['fps_potential']:.1f} FPS)"
                    )

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
    test_grayscale_handler()
