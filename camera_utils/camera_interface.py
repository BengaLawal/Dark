import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, Optional


class Camera(ABC):
    """Abstract base class for camera implementations"""

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the camera

        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def capture_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Capture a single frame

        Returns:
            Tuple[bool, Optional[np.ndarray]]: Success flag and frame data if successful
        """
        pass

    @abstractmethod
    def start_video_recording(self) -> bool:
        """
        Start recording video

        Returns:
            bool: True if recording started successfully, False otherwise
        """
        pass

    @abstractmethod
    def stop_video_recording(self) -> Optional[str]:
        """
        Stop video recording

        Returns:
            Optional[str]: Path to the recorded video file if successful, None otherwise
        """
        pass

    @abstractmethod
    def is_recording(self) -> bool:
        """
        Check if camera is currently recording

        Returns:
            bool: True if recording is in progress, False otherwise
        """
        pass

    @abstractmethod
    def get_recording_duration(self) -> float:
        """
        Get the duration of the current recording

        Returns:
            float: Duration in seconds, 0.0 if not recording
        """
        pass

    @abstractmethod
    def release(self) -> None:
        """Release camera resources"""
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """
        Check if camera is properly initialized

        Returns:
            bool: True if camera is initialized and ready, False otherwise
        """
        pass