import cv2
import numpy as np
import time
from PIL import Image

from camera_utils.camera_canon import CanonCamera
from camera_utils.camera_interface import Camera
from typing import Tuple, List, Optional, Any

from file_manager import FileManager, MediaType


class CameraManager:
    """Manager class to handle camera operations and processing"""

    def __init__(self, camera: Camera):
        self.camera = camera
        self.recording_frames = []

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

    def start_video_recording(self) -> bool:
        """Start video recording"""
        self.recording_frames = []  # Clear any existing frames
        return self.camera.start_video_recording()

    def stop_video_recording(self) -> Optional[str]:
        """Stop video recording and return the video file path"""
        return self.camera.stop_video_recording()

    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self.camera.is_recording()

    def get_recording_duration(self) -> float:
        """Get current recording duration"""
        return self.camera.get_recording_duration()

    def capture_boomerang_sequence(self, duration: float, fps: int = 30) -> List[np.ndarray]:
        """Capture a sequence of frames for boomerang"""
        frames = []
        start_time = time.time()
        frame_interval = 1.0 / fps

        while time.time() - start_time < duration:
            ret, frame = self.camera.capture_frame()
            if ret:
                frames.append(frame)
            time.sleep(frame_interval)

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

    def capture_picture(self) -> Optional[Any]:
        """Capture a single picture using camera's native capture"""
        if isinstance(self.camera, CanonCamera):
            return self.camera.capture_picture()
        else:
            # Fallback for other camera types
            ret, frame = self.camera.capture_frame()
            if not ret:
                return None

            count = FileManager.increment_count(MediaType.PICTURE)
            target_path = FileManager.get_save_path(MediaType.PICTURE, count)

            # Save the captured frame
            cv2.imwrite(target_path, frame)
            return target_path