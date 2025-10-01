# Face Detection Library
from .face_detection import FaceDetector, create_face_detector, test_face_detection

# Grayscale Handler
from .grayscale_handler import (
    GrayscaleHandler,
    create_grayscale_handler,
    quick_grayscale,
)

# Compression Handler
from .compression_handler import (
    CompressionHandler,
    CompressionFormat,
    create_compression_handler,
    quick_jpeg_compress,
)

__version__ = "1.0.0"
__all__ = [
    # Face Detection
    "FaceDetector",
    "create_face_detector",
    "test_face_detection",
    # Grayscale
    "GrayscaleHandler",
    "create_grayscale_handler",
    "quick_grayscale",
    # Compression
    "CompressionHandler",
    "CompressionFormat",
    "create_compression_handler",
    "quick_jpeg_compress",
]
