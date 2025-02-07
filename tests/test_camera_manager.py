import pytest
import numpy as np
from unittest.mock import Mock, patch
from PIL import Image
from camera_utils.camera_manager import CameraManager
from camera_utils.camera_interface import Camera


@pytest.fixture
def mock_camera():
    camera = Mock(spec=Camera)
    camera.initialize.return_value = True
    camera.is_recording.return_value = False
    camera.get_recording_duration.return_value = 0.0
    return camera


@pytest.fixture
def camera_manager(mock_camera):
    return CameraManager(mock_camera)


def test_initialize_camera(camera_manager, mock_camera):
    assert camera_manager.initialize_camera() is True
    mock_camera.initialize.assert_called_once()


def test_capture_and_process_frame(camera_manager, mock_camera):
    # test frame
    test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_camera.capture_frame.return_value = (True, test_frame)

    # Test without preview size
    result = camera_manager.capture_and_process_frame()
    assert isinstance(result, Image.Image)
    assert result.size == (100, 100)

    # Test with preview size
    preview_size = (50, 50)
    result = camera_manager.capture_and_process_frame(preview_size)
    assert isinstance(result, Image.Image)
    assert result.size == preview_size


def test_capture_and_process_frame_failure(camera_manager, mock_camera):
    mock_camera.capture_frame.return_value = (False, None)
    result = camera_manager.capture_and_process_frame()
    assert result is None


def test_video_recording(camera_manager, mock_camera):
    # Test start recording
    mock_camera.start_video_recording.return_value = True
    assert camera_manager.start_video_recording() is True
    assert camera_manager.recording_frames == []

    # Test stop recording
    expected_path = "/path/to/video.mp4"
    mock_camera.stop_video_recording.return_value = expected_path
    assert camera_manager.stop_video_recording() == expected_path


def test_recording_status(camera_manager, mock_camera):
    mock_camera.is_recording.return_value = True
    assert camera_manager.is_recording() is True

    mock_camera.get_recording_duration.return_value = 2.5
    assert camera_manager.get_recording_duration() == 2.5


@patch('time.time')
@patch('time.sleep')
def test_capture_boomerang_sequence(mock_sleep, mock_time, camera_manager, mock_camera):
    # Mock time to control the duration
    mock_time.side_effect = [0, 0.1, 0.2, 0.3]
    
    # Create test frames
    test_frames = [
        np.zeros((100, 100, 3), dtype=np.uint8),
        np.ones((100, 100, 3), dtype=np.uint8) * 255
    ]
    mock_camera.capture_frame.side_effect = [(True, frame) for frame in test_frames]

    result = camera_manager.capture_boomerang_sequence(0.3)
    
    # Check if the boomerang sequence is correct (forward-backward-forward)
    assert len(result) == len(test_frames) * 3
    # Check first sequence (forward)
    assert np.array_equal(result[0], test_frames[0])
    assert np.array_equal(result[1], test_frames[1])
    # Check second sequence (backward)
    assert np.array_equal(result[2], test_frames[1])
    assert np.array_equal(result[3], test_frames[0])
    # Check third sequence (forward)
    assert np.array_equal(result[4], test_frames[0])
    assert np.array_equal(result[5], test_frames[1])


def test_release_camera(camera_manager, mock_camera):
    camera_manager.release_camera()
    mock_camera.release.assert_called_once()
