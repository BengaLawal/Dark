import pytest
import cv2
import numpy as np
import time
from unittest.mock import Mock, patch, MagicMock
from camera_utils.camera_opencv import OpenCVCamera
import logging

@pytest.fixture
def mock_logger():
    return logging.getLogger('test_logger')

@pytest.fixture
def opencv_camera(mock_logger):
    return OpenCVCamera(camera_index=0, logger=mock_logger)

def test_initialize_success(opencv_camera):
    with patch('cv2.VideoCapture') as mock_capture:
        mock_capture.return_value.isOpened.return_value = True
        mock_capture.return_value.set.return_value = True
        
        assert opencv_camera.initialize() is True
        assert opencv_camera.is_initialized() is True
        
        # Verify camera settings
        mock_capture.return_value.set.assert_any_call(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        mock_capture.return_value.set.assert_any_call(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        mock_capture.return_value.set.assert_any_call(cv2.CAP_PROP_FPS, 30)

def test_initialize_failure(opencv_camera):
    with patch('cv2.VideoCapture') as mock_capture:
        mock_capture.return_value.isOpened.return_value = False
        
        assert opencv_camera.initialize() is False
        assert opencv_camera.is_initialized() is False

def test_capture_frame_success(opencv_camera):
    with patch('cv2.VideoCapture') as mock_capture:
        # Create test frame
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_capture.return_value.read.return_value = (True, test_frame)
        mock_capture.return_value.isOpened.return_value = True
        
        opencv_camera.cap = mock_capture.return_value
        
        success, frame = opencv_camera.capture_frame()
        assert success is True
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)

def test_capture_frame_not_initialized(opencv_camera):
    success, frame = opencv_camera.capture_frame()
    assert success is False
    assert frame is None

def test_start_video_recording(opencv_camera):
    with patch('cv2.VideoCapture') as mock_capture, \
         patch('cv2.VideoWriter') as mock_writer:
        
        mock_capture.return_value.get.side_effect = [1920, 1080, 30]
        mock_capture.return_value.isOpened.return_value = True
        opencv_camera.cap = mock_capture.return_value
        
        assert opencv_camera.start_video_recording() is True
        assert opencv_camera.is_recording() is True
        assert opencv_camera.video_writer is not None

def test_stop_video_recording(opencv_camera):
    with patch('cv2.VideoWriter') as mock_writer:
        opencv_camera._recording = True
        opencv_camera.video_writer = mock_writer.return_value
        opencv_camera.video_path = "./videos/test_video.mp4"
        
        result = opencv_camera.stop_video_recording()
        assert result == "./videos/test_video.mp4"
        assert opencv_camera.is_recording() is False
        assert opencv_camera.video_writer is None
        mock_writer.return_value.release.assert_called_once()

def test_get_recording_duration(opencv_camera):
    opencv_camera._recording = True
    opencv_camera.video_start_time = time.time() - 5  # Simulate 5 seconds of recording
    
    duration = opencv_camera.get_recording_duration()
    assert 4.9 <= duration <= 5.1

def test_release(opencv_camera):
    with patch('cv2.VideoCapture') as mock_capture:
        opencv_camera.cap = mock_capture.return_value
        opencv_camera._recording = False
        
        opencv_camera.release()
        
        mock_capture.return_value.release.assert_called_once()
        assert opencv_camera.cap is None

def test_is_initialized(opencv_camera):
    with patch('cv2.VideoCapture') as mock_capture:
        mock_capture.return_value.isOpened.return_value = True
        opencv_camera.cap = mock_capture.return_value
        
        assert opencv_camera.is_initialized() is True
        
        mock_capture.return_value.isOpened.return_value = False
        assert opencv_camera.is_initialized() is False

def test_recording_frame_capture(opencv_camera):
    with patch('cv2.VideoCapture') as mock_capture, \
         patch('cv2.VideoWriter') as mock_writer:
        
        # Setup recording state
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_capture.return_value.read.return_value = (True, test_frame)
        mock_capture.return_value.isOpened.return_value = True
        
        opencv_camera.cap = mock_capture.return_value
        opencv_camera._recording = True
        opencv_camera.video_writer = mock_writer.return_value
        
        # Capture frame while recording
        success, frame = opencv_camera.capture_frame()
        
        assert success is True
        mock_writer.return_value.write.assert_called_once_with(test_frame)
