from abc import ABC, abstractmethod
import cv2
import numpy as np
from PIL import Image
import time
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)

class Camera(ABC):
    """Abstract base class for camera implementations"""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the camera"""
        pass

    @abstractmethod
    def capture_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Capture a single frame"""
        pass

    @abstractmethod
    def release(self) -> None:
        """Release camera resources"""
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if camera is properly initialized"""
        pass


class OpenCVCamera(Camera):
    """OpenCV implementation of the camera interface"""

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap = None

    def initialize(self, ) -> bool:
        """Initialize the OpenCV camera with retry mechanism"""
        max_retries = 3
        for retry_count in range(max_retries):
            try:
                self.cap = cv2.VideoCapture(self.camera_index)
                if self.cap.isOpened():
                    return True
                time.sleep(1)
            except Exception as e:
                print(f"Camera initialization attempt {retry_count + 1} failed: {e}")
        return False

    def capture_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Capture a frame from the OpenCV camera"""
        if not self.is_initialized():
            return False, None
        return self.cap.read()

    def release(self) -> None:
        """Release OpenCV camera resources"""
        if self.cap:
            self.cap.release()
            self.cap = None

    def is_initialized(self) -> bool:
        """Check if OpenCV camera is initialized and opened"""
        return self.cap is not None and self.cap.isOpened()


class CameraManager:
    """Manager class to handle camera operations and processing"""

    def __init__(self, camera: Camera):
        self.camera = camera

    def initialize_camera(self) -> bool:
        """Initialize the camera"""
        return self.camera.initialize()

    def capture_and_process_frame(self, preview_size: Optional[Tuple[int, int]] = None) -> Optional[Image.Image]:
        """Capture and process a frame, optionally resizing for preview"""
        ret, frame = self.camera.capture_frame()
        if not ret:
            return None

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)

        # Resize if preview size is specified
        if preview_size:
            pil_image = pil_image.resize(preview_size)

        return pil_image

    def capture_video_sequence(self, duration: float, fps: int = 30) -> List[np.ndarray]:
        """Capture a sequence of frames for video"""
        frames = []
        start_time = time.time()
        frame_interval = 1.0 / fps

        while time.time() - start_time < duration:
            ret, frame = self.camera.capture_frame()
            if ret:
                frames.append(frame)
            time.sleep(frame_interval)

        return frames

    def capture_boomerang_sequence(self, duration: float, fps: int = 30) -> List[np.ndarray]:
        """Capture a sequence of frames for boomerang"""
        frames = self.capture_video_sequence(duration, fps)
        return self._arrange_boomerang_frames(frames)

    @staticmethod
    def _arrange_boomerang_frames(frames: List[np.ndarray]) -> List[np.ndarray]:
        """Arrange frames for boomerang effect"""
        complete_boomerang = []
        for i in range(3):
            sequence = frames if i % 2 == 0 else frames[::-1]
            complete_boomerang.extend(sequence)
        return complete_boomerang

    def release_camera(self) -> None:
        """Release camera resources"""
        self.camera.release()