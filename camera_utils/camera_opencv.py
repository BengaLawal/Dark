import time
import cv2
import numpy as np
from typing import Tuple, Optional
from camera_utils.camera_interface import Camera


class OpenCVCamera(Camera):
    """OpenCV implementation of the camera interface"""

    def __init__(self, camera_index: int = 0, logger=None):
        self.camera_index = camera_index
        self.cap = None
        self.logger = logger.getChild(self.__class__.__name__)
        self._recording = False
        self.video_writer = None
        self.video_path = None
        self.video_start_time = None

    def initialize(self) -> bool:
        """Initialize the OpenCV camera with retry mechanism"""
        max_retries = 3
        for retry_count in range(max_retries):
            try:
                self.cap = cv2.VideoCapture(self.camera_index)
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    self.logger.info("OpenCV camera initialized successfully")
                    return True
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Camera initialization attempt {retry_count + 1} failed: {e}")
        return False

    def capture_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Capture a frame from the OpenCV camera"""
        if not self.is_initialized():
            return False, None

        ret, frame = self.cap.read()

        if ret and self._recording and self.video_writer:
            self.video_writer.write(frame)

        return ret, frame

    def start_video_recording(self) -> bool:
        """Start recording video"""
        if not self.is_initialized() or self._recording:
            return False

        try:
            # Get camera properties
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self.cap.get(cv2.CAP_PROP_FPS))

            # Create video writer
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.video_path = f"./videos/opencv_video_{timestamp}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                self.video_path,
                fourcc,
                fps,
                (width, height)
            )

            self._recording = True
            self.video_start_time = time.time()
            return True

        except Exception as e:
            self.logger.error(f"Failed to start video recording: {e}")
            return False

    def stop_video_recording(self) -> Optional[str]:
        """Stop recording video and return the file path"""
        if not self._recording or self.video_writer is None:
            return None

        try:
            self.video_writer.release()
            self.video_writer = None
            self._recording = False
            return self.video_path

        except Exception as e:
            self.logger.error(f"Failed to stop video recording: {e}")
            return None

    def is_recording(self) -> bool:
        """Check if currently recording video"""
        return self._recording

    def get_recording_duration(self) -> float:
        """Get current recording duration in seconds"""
        if not self._recording or self.video_start_time is None:
            return 0.0
        return time.time() - self.video_start_time

    def release(self) -> None:
        """Release OpenCV camera resources"""
        if self._recording:
            self.stop_video_recording()
        if self.cap:
            self.cap.release()
            self.cap = None

    def is_initialized(self) -> bool:
        """Check if OpenCV camera is initialized and opened"""
        return self.cap is not None and self.cap.isOpened()