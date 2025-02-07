import pytest
import os
import json
from unittest.mock import patch, mock_open, MagicMock
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import configuration as config


@pytest.fixture
def mock_credentials():
    """Fixture to create mock credentials"""
    creds = MagicMock(spec=Credentials)
    creds.valid = True
    creds.expired = False
    creds.to_json.return_value = json.dumps({"token": "test_token"})
    return creds


@pytest.fixture
def mock_flow():
    """Fixture to create mock OAuth flow"""
    flow = MagicMock()
    flow.run_local_server.return_value = MagicMock(spec=Credentials)
    return flow


def test_check_if_token_exist_with_existing_token(mock_credentials):
    """Test token check when token file exists"""
    with patch('os.path.exists') as mock_exists, \
            patch('google.oauth2.credentials.Credentials.from_authorized_user_file') as mock_from_file:
        mock_exists.return_value = True
        mock_from_file.return_value = mock_credentials

        result = config.check_if_token_exist()

        assert result is not None
        mock_exists.assert_called_once_with(config.TOKEN_FILE)
        mock_from_file.assert_called_once_with(config.TOKEN_FILE, config.SCOPES)


def test_check_if_token_exist_without_token():
    """Test token check when token file doesn't exist"""
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False

        result = config.check_if_token_exist()

        assert result is None
        mock_exists.assert_called_once_with(config.TOKEN_FILE)


def test_save_token(mock_credentials):
    """Test token saving functionality"""
    mock_file = mock_open()
    test_path = "/test/path/token.json"

    with patch('builtins.open', mock_file), \
            patch('os.makedirs') as mock_makedirs, \
            patch('os.chmod') as mock_chmod:
        config.save_token(mock_credentials, test_path)

        mock_makedirs.assert_called_once_with(os.path.dirname(test_path), exist_ok=True)
        mock_file.assert_called_once_with(test_path, 'w')
        mock_file().write.assert_called_once_with(mock_credentials.to_json())
        mock_chmod.assert_called_once_with(test_path, 0o600)


@pytest.mark.parametrize("creds_state", [
    {"valid": True, "expired": False},  # Valid credentials
    {"valid": False, "expired": False}  # Invalid credentials requiring new flow
])
def test_login(creds_state, mock_credentials, mock_flow):
    """Test login function with different credential states"""
    mock_credentials.valid = creds_state["valid"]
    mock_credentials.expired = creds_state["expired"]

    with patch('config.configuration.check_if_token_exist') as mock_check, \
            patch('config.configuration.save_token') as mock_save, \
            patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file') as mock_flow_create:

        mock_check.return_value = mock_credentials if any(creds_state.values()) else None
        mock_flow_create.return_value = mock_flow

        result = config.login()

        mock_check.assert_called_once()

        if not creds_state["valid"]:
            if creds_state["expired"] and mock_credentials.refresh_token:
                mock_credentials.refresh.assert_called_once_with(Request())
            else:
                mock_flow_create.assert_called_once_with(config.CREDENTIALS_FILE, config.SCOPES)
                mock_flow.run_local_server.assert_called_once_with(port=0)
            mock_save.assert_called_once()

        assert result is not None


@pytest.mark.parametrize("exception_type", [
    OSError,
    ValueError,
    FileNotFoundError
])
def test_save_token_error_handling(mock_credentials, exception_type):
    """Test error handling in save_token function"""
    test_path = "/test/path/token.json"

    with patch('builtins.open', mock_open()) as mock_file, \
            patch('os.makedirs') as mock_makedirs:
        mock_makedirs.side_effect = exception_type("Test error")

        with pytest.raises(exception_type):
            config.save_token(mock_credentials, test_path)