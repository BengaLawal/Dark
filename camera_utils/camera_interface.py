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