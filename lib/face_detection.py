#!/usr/bin/python3
"""
Face Detection Library for Raspberry Pi streaming
Lightweight OpenCV-based face detection with memory optimization
"""

import cv2  # pyright: ignore[reportMissingImports]
import time


class FaceDetector:
    def __init__(
        self,
        detection_interval=1.0,  # Detect faces every 1 second (not every frame)
        min_face_size=(30, 30),  # Minimum face size for Pi Zero performance
        scale_factor=1.05,  # More precise scale factor for accuracy
        min_neighbors=4,  # Higher neighbors for better accuracy
        max_detection_size=(240, 180),  # Larger processing size for accuracy
    ):
        self.detection_interval = detection_interval
        self.min_face_size = min_face_size
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.max_detection_size = max_detection_size

        # Face detection state
        self.faces_detected = []
        self.last_detection_time = 0
        self.detection_enabled = True
        self.stats = {"total_detections": 0, "faces_found": 0, "avg_processing_time": 0}

        # Load face cascade (try different paths for different systems)
        self.face_cascade = None
        self._load_cascade()

        print(
            f"Face detector initialized: interval={detection_interval}s, min_size={min_face_size}, max_size={max_detection_size}"
        )

    def _load_cascade(self):
        """Load Haar cascade for face detection"""
        cascade_paths = [
            "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
            "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
            "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
            "/usr/local/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
            "haarcascades/haarcascade_frontalface_default.xml",
        ]

        # Try to add cv2.data.haarcascades path if it exists
        try:
            if hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
                cascade_paths.insert(
                    0, cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )
        except AttributeError:
            pass  # cv2.data not available, skip this path

        for path in cascade_paths:
            try:
                self.face_cascade = cv2.CascadeClassifier(path)
                if not self.face_cascade.empty():
                    print(f"✓ Loaded face cascade from: {path}")
                    return True
            except Exception:
                continue

        print("✗ Could not load face cascade classifier!")
        print("Try downloading manually:")
        print(
            "sudo wget -O /usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml \\"
        )
        print(
            "  https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
        )
        self.face_cascade = None
        return False

    def is_available(self):
        """Check if face detection is available"""
        return self.face_cascade is not None and not self.face_cascade.empty()

    def enable(self):
        """Enable face detection"""
        self.detection_enabled = True
        print("Face detection enabled")

    def disable(self):
        """Disable face detection"""
        self.detection_enabled = False
        print("Face detection disabled")

    def should_detect(self):
        """Check if it's time to run face detection"""
        if not self.detection_enabled or not self.is_available():
            return False

        current_time = time.time()
        return (current_time - self.last_detection_time) >= self.detection_interval

    def detect_faces(self, frame):
        """
        Detect faces in a frame (lightweight version for Pi Zero)

        Args:
            frame: OpenCV image frame (BGR format)

        Returns:
            list: List of face rectangles (x, y, w, h)
        """
        if not self.should_detect():
            return self.faces_detected  # Return cached results

        start_time = time.time()

        try:
            # Convert to grayscale for faster processing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Apply histogram equalization for better contrast and accuracy
            gray = cv2.equalizeHist(gray)

            # Intelligent resizing for better accuracy vs performance balance
            height, width = gray.shape
            max_width, max_height = self.max_detection_size

            if width > max_width or height > max_height:
                # Scale to fit within max detection size while maintaining aspect ratio
                scale_w = max_width / width
                scale_h = max_height / height
                scale = min(scale_w, scale_h)

                new_width = int(width * scale)
                new_height = int(height * scale)
                gray_small = cv2.resize(
                    gray, (new_width, new_height), interpolation=cv2.INTER_AREA
                )
            else:
                gray_small = gray
                scale = 1.0

            # More accurate face detection with optimized parameters
            faces = self.face_cascade.detectMultiScale(
                gray_small,
                scaleFactor=self.scale_factor,  # Smaller steps for more precision
                minNeighbors=self.min_neighbors,  # Higher threshold for accuracy
                minSize=(
                    int(self.min_face_size[0] * scale),
                    int(self.min_face_size[1] * scale),
                ),
                maxSize=(
                    int(min(new_width, new_height) * 0.8),
                    int(min(new_width, new_height) * 0.8),
                ),
                flags=cv2.CASCADE_DO_CANNY_PRUNING
                | cv2.CASCADE_SCALE_IMAGE,  # Accuracy + performance flags
            )

            # Filter and validate detected faces for better accuracy
            validated_faces = []
            for x, y, w, h in faces:
                # Scale coordinates back to original size
                if scale != 1.0:
                    x, y, w, h = (
                        int(x / scale),
                        int(y / scale),
                        int(w / scale),
                        int(h / scale),
                    )

                # Validate face dimensions (aspect ratio check)
                aspect_ratio = w / h
                if 0.7 <= aspect_ratio <= 1.4:  # Reasonable face aspect ratio
                    # Ensure face is not too small or too large
                    face_area = w * h
                    frame_area = width * height
                    relative_size = face_area / frame_area

                    if 0.01 <= relative_size <= 0.5:  # Face should be 1-50% of frame
                        validated_faces.append((x, y, w, h))

            # Update state with validated faces
            self.faces_detected = validated_faces
            self.last_detection_time = time.time()

            # Update statistics
            processing_time = (self.last_detection_time - start_time) * 1000
            self.stats["total_detections"] += 1
            self.stats["faces_found"] += len(validated_faces)

            # Running average of processing time
            if self.stats["avg_processing_time"] == 0:
                self.stats["avg_processing_time"] = processing_time
            else:
                self.stats["avg_processing_time"] = (
                    self.stats["avg_processing_time"] * 0.8 + processing_time * 0.2
                )

            if len(validated_faces) > 0:
                print(
                    f"Detected {len(validated_faces)} face(s) in {processing_time:.1f}ms"
                )

            return validated_faces

        except Exception as e:
            print(f"Face detection error: {e}")
            return []

    def draw_faces(self, frame, faces=None):
        """
        Draw rectangles around detected faces

        Args:
            frame: OpenCV image frame
            faces: List of face rectangles (optional, uses cached if None)

        Returns:
            frame: Frame with face rectangles drawn
        """
        if faces is None:
            faces = self.faces_detected

        if len(faces) == 0:
            return frame

        # Draw rectangles around faces
        for x, y, w, h in faces:
            # Green rectangle for faces
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Add face count text
            cv2.putText(
                frame,
                "Face",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
            )

        # Add detection info
        info_text = (
            f"Faces: {len(faces)} | Detections: {self.stats['total_detections']}"
        )
        cv2.putText(
            frame,
            info_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        return frame

    def get_stats(self):
        """Get face detection statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {"total_detections": 0, "faces_found": 0, "avg_processing_time": 0}
        print("Face detection stats reset")


class FaceDetectionCallback:
    """Callback interface for face detection events"""

    def __init__(self, detector):
        self.detector = detector
        self.callbacks = []

    def add_callback(self, callback_func):
        """Add a callback function for when faces are detected"""
        self.callbacks.append(callback_func)

    def on_faces_detected(self, faces, frame_info=None):
        """Called when faces are detected"""
        for callback in self.callbacks:
            try:
                callback(faces, frame_info)
            except Exception as e:
                print(f"Callback error: {e}")


# Helper functions for integration
def create_face_detector(lightweight=True):
    """
    Create a face detector with optimal settings

    Args:
        lightweight: If True, use Pi Zero 2 W optimized settings
    """
    if lightweight:
        return FaceDetector(
            detection_interval=1.5,  # Balanced frequency for accuracy
            min_face_size=(25, 25),  # Smaller faces for better detection
            scale_factor=1.08,  # More precise scaling for accuracy
            min_neighbors=3,  # Balanced accuracy vs false positives
            max_detection_size=(200, 150),  # Larger processing for better accuracy
        )
    else:
        return FaceDetector(
            detection_interval=0.5,  # Every 500ms for faster Pi
            min_face_size=(30, 30),
            scale_factor=1.05,  # Very precise for maximum accuracy
            min_neighbors=4,  # Higher threshold for accuracy
            max_detection_size=(240, 180),  # Even larger processing size
        )


def test_face_detection():
    """Test function for face detection"""
    print("Testing face detection...")

    detector = create_face_detector(lightweight=True)

    if not detector.is_available():
        print("Face detection not available!")
        return False

    # Test with camera if available
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Camera not available for testing")
            return False

        print("Press 'q' to quit, 't' to toggle detection")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect faces
            faces = detector.detect_faces(frame)

            # Draw faces
            frame = detector.draw_faces(frame, faces)

            # Show frame
            cv2.imshow("Face Detection Test", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("t"):
                if detector.detection_enabled:
                    detector.disable()
                else:
                    detector.enable()

        cap.release()
        cv2.destroyAllWindows()

        # Show stats
        stats = detector.get_stats()
        print(f"Final stats: {stats}")

        return True

    except Exception as e:
        print(f"Test error: {e}")
        return False


if __name__ == "__main__":
    test_face_detection()
