import os
import io
import time
import subprocess
import gphoto2 as gp
from PIL import Image
from typing import Tuple, Optional
from camera_utils.camera_interface import Camera


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
            self._kill_gphoto2_process()

            max_retries = 3
            for attempt in range(max_retries):
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

                except Exception as gp_err:
                    self.logger.warning(f"GPhoto error on attempt {attempt + 1}: {gp_err}")
                    if attempt < max_retries - 1:
                        self._reset_usb()
                        time.sleep(2)
                    else:
                        raise

            return False

        except Exception as e:
            self.logger.error(f"Failed to initialize Canon camera: {e}")
            self._initialized = False
            return False

    def capture_frame(self) -> Tuple[bool, Optional[Image.Image]]:
        """Capture a preview frame as PIL Image"""
        if not self.is_initialized():
            return False, None

        try:
            preview_file = self.camera.capture_preview()
            preview_data = preview_file.get_data_and_size()
            image = Image.open(io.BytesIO(preview_data))
            return True, image

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
            self.logger.info("Started video recording on Canon camera")
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
            time.sleep(2)

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

    def _kill_gphoto2_process(self) -> None:
        """Kill any existing gphoto2 processes that might be blocking camera access"""
        try:
            # List of processes to kill
            processes = [
                "gvfs-gphoto2-volume-monitor",
                "gvfsd-gphoto2",
                "gvfs-afc-volume-monitor"
            ]

            for process in processes:
                try:
                    # Try using pkill
                    subprocess.run(['pkill', '-f', process],
                                   stderr=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL)
                except subprocess.SubprocessError:
                    try:
                        # Alternative using killall
                        subprocess.run(['killall', process],
                                       stderr=subprocess.DEVNULL,
                                       stdout=subprocess.DEVNULL)
                    except subprocess.SubprocessError:
                        pass

            # Short delay to ensure processes are terminated
            time.sleep(1)

        except Exception as e:
            self.logger.warning(f"Error while killing gphoto2 processes: {e}")

    def _reset_usb(self) -> None:
        """Reset USB device if camera is not responding"""
        try:
            # Find Canon camera USB device
            lsusb_output = subprocess.check_output(['lsusb']).decode()
            for line in lsusb_output.split('\n'):
                if 'Canon' in line:
                    # Extract bus and device numbers
                    bus = line.split()[1]
                    device = line.split()[3].rstrip(':')

                    # Reset USB device
                    subprocess.run(['sudo', 'usbreset', f'/dev/bus/usb/{bus}/{device}'],
                                   stderr=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL)
                    time.sleep(2)
                    break
        except Exception as e:
            self.logger.warning(f"Error while resetting USB: {e}")

    def capture_picture(self) -> Optional[str]:
        """Capture picture directly to memory card using gphoto2"""
        try:
            if not self.is_initialized():
                return None

            # Capture image to camera's memory card
            file_path = self.camera.capture(gp.GP_CAPTURE_IMAGE)

            # Get the file from camera
            camera_file = self.camera.file_get(
                file_path.folder,
                file_path.name,
                gp.GP_FILE_TYPE_NORMAL
            )
            return camera_file

        except Exception as e:
            self.logger.error(f"Failed to capture picture: {e}")
            return None

    def capture_and_process_frame(self, preview_size: Optional[Tuple[int, int]] = None) -> Optional[Image.Image]:
        """Capture and optionally resize a preview frame"""
        ret, image = self.capture_frame()
        if not ret or image is None:
            return None

        if preview_size:
            image = image.resize(preview_size)
        return image
