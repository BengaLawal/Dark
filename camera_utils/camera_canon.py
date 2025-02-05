import gphoto2 as gp
import numpy as np
from PIL import Image
import io
from typing import Tuple, List, Optional
from camera_utils.camera_interface import Camera
import time
import cv2


class CanonCamera(Camera):
    """Canon EOS camera implementation using gphoto2"""

    def __init__(self, logger=None):
        self.camera = None
        self.context = None
        self.logger = logger.getChild(self.__class__.__name__)
        self._initialized = False
        self._recording = False
        self.video_start_time = None

    def initialize(self) -> bool:
        """Initialize the Canon camera using gphoto2"""
        try:
            self.context = gp.Context()
            self.camera = gp.Camera()
            self.camera.init(self.context)

            # Configure camera settings
            config = self.camera.get_config(self.context)
            capture_target = config.get_child_by_name('capturetarget')
            capture_target.set_value('Memory card')
            self.camera.set_config(config, self.context)

            self._initialized = True
            self.logger.info("Canon camera initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Canon camera: {e}")
            self._initialized = False
            return False

    def capture_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Capture a frame from the Canon camera"""
        if not self.is_initialized():
            return False, None

        try:
            # If we're recording video, return the preview frame
            preview_file = self.camera.capture_preview()
            preview_data = preview_file.get_data_and_size()

            image = Image.open(io.BytesIO(preview_data))
            frame = np.array(image)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            return True, frame_bgr

        except Exception as e:
            self.logger.error(f"Failed to capture frame: {e}")
            return False, None

    def start_video_recording(self) -> bool:
        """Start video recording on the camera"""
        try:
            config = self.camera.get_config()
            movie_record = config.get_child_by_name('movie')
            movie_record.set_value(1)
            self.camera.set_config(config)
            self._recording = True
            self.video_start_time = time.time()
            return True
        except Exception as e:
            self.logger.error(f"Failed to start video recording: {e}")
            return False

    def stop_video_recording(self) -> Optional[str]:
        """Stop video recording and return the video file path"""
        if not self._recording:
            return None

        try:
            config = self.camera.get_config()
            movie_record = config.get_child_by_name('movie')
            movie_record.set_value(0)
            self.camera.set_config(config)

            # Wait briefly for the camera to finish writing
            time.sleep(1)

            # Get the latest video file
            folder_list = self.camera.folder_list_files('/')
            video_files = [f for f in folder_list if f.lower().endswith(('.mp4', '.mov'))]
            if video_files:
                latest_video = video_files[-1]

                # Download the video file
                camera_file = self.camera.file_get(
                    '/',
                    latest_video,
                    gp.GP_FILE_TYPE_NORMAL
                )

                # Save to local storage
                local_path = f"./videos/{latest_video}"
                camera_file.save(local_path)

                self._recording = False
                return local_path

        except Exception as e:
            self.logger.error(f"Failed to stop video recording: {e}")

        self._recording = False
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
        """Release Canon camera resources"""
        if self._recording:
            self.stop_video_recording()
        if self.camera:
            self.camera.exit()
            self.camera = None
            self.context = None
            self._initialized = False

    def is_initialized(self) -> bool:
        """Check if Canon camera is properly initialized"""
        return self._initialized