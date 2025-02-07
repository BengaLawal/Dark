import pytest
import time
import gphoto2 as gp
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from camera_utils.camera_canon import CanonCamera
from PIL import Image
import io
import logging

@pytest.fixture
def mock_logger():
    return logging.getLogger('test_logger')

@pytest.fixture
def canon_camera(mock_logger):
    return CanonCamera(logger=mock_logger)

def test_initialize_success(canon_camera):
    with patch('gphoto2.Camera') as mock_camera, \
         patch('gphoto2.Context') as mock_context:
        
        # Setup mock camera configuration
        mock_config = MagicMock()
        mock_capture_target = MagicMock()
        mock_config.get_child_by_name.return_value = mock_capture_target
        mock_camera.return_value.get_config.return_value = mock_config

        assert canon_camera.initialize() is True
        assert canon_camera.is_initialized() is True
        mock_camera.return_value.init.assert_called_once()

def test_initialize_failure(canon_camera):
    with patch('gphoto2.Camera') as mock_camera:
        mock_camera.return_value.init.side_effect = Exception("Camera init failed")
        
        assert canon_camera.initialize() is False
        assert canon_camera.is_initialized() is False

def test_capture_frame_success(canon_camera):
    with patch('gphoto2.Camera') as mock_camera:
        # Mock successful initialization
        canon_camera._initialized = True
        canon_camera.camera = mock_camera.return_value

        # Create a small test image
        test_image = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = io.BytesIO()
        test_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # Mock preview capture
        mock_preview = MagicMock()
        mock_preview.get_data_and_size.return_value = img_byte_arr
        mock_camera.return_value.capture_preview.return_value = mock_preview

        success, frame = canon_camera.capture_frame()
        assert success is True
        assert isinstance(frame, np.ndarray)
        assert frame.shape[2] == 3  # Should be BGR format

def test_capture_frame_not_initialized(canon_camera):
    success, frame = canon_camera.capture_frame()
    assert success is False
    assert frame is None

def test_start_video_recording(canon_camera):
    with patch('gphoto2.Camera') as mock_camera:
        # Setup mock configuration
        mock_config = MagicMock()
        mock_movie = MagicMock()
        mock_config.get_child_by_name.return_value = mock_movie
        mock_camera.return_value.get_config.return_value = mock_config
        
        canon_camera.camera = mock_camera.return_value
        
        assert canon_camera.start_video_recording() is True
        assert canon_camera.is_recording() is True
        mock_movie.set_value.assert_called_with(1)

def test_stop_video_recording(canon_camera):
    with patch('gphoto2.Camera') as mock_camera:
        # Setup mock configuration
        mock_config = MagicMock()
        mock_movie = MagicMock()
        mock_config.get_child_by_name.return_value = mock_movie
        mock_camera.return_value.get_config.return_value = mock_config
        
        # Mock file operations
        mock_camera.return_value.folder_list_files.return_value = ['test.mp4']
        mock_file = MagicMock()
        mock_camera.return_value.file_get.return_value = mock_file
        
        canon_camera.camera = mock_camera.return_value
        canon_camera._recording = True
        
        result = canon_camera.stop_video_recording()
        assert result == './videos/test.mp4'
        assert canon_camera.is_recording() is False
        mock_movie.set_value.assert_called_with(0)

def test_get_recording_duration(canon_camera):
    canon_camera._recording = True
    canon_camera.video_start_time = time.time() - 5  # Simulate 5 seconds of recording
    
    duration = canon_camera.get_recording_duration()
    assert 4.9 <= duration <= 5.1  # Allow small time difference

def test_release(canon_camera):
    mock_camera = MagicMock()
    canon_camera.camera = mock_camera
    canon_camera._initialized = True
    
    canon_camera.release()
    
    mock_camera.exit.assert_called_once()
    assert canon_camera.camera is None
    assert canon_camera.context is None
    assert canon_camera._initialized is False
