import base64
import pytest
from unittest.mock import Mock, patch, mock_open
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from googleapiclient.errors import HttpError
from mail import EmailSender


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def email_sender(mock_logger):
    with patch.dict('os.environ', {'SENDER_EMAIL': 'test@example.com'}):
        return EmailSender(mock_logger)


@pytest.fixture
def mock_credentials():
    return Mock()


@pytest.fixture
def mock_service():
    service = Mock()
    service.users().messages().send.return_value.execute.return_value = {'id': '123'}
    return service

@pytest.mark.parametrize("file_content,content_type,expected_mime_class", [
    (b'test content', 'text/plain', MIMEText),
    (b'image content', 'image/jpeg', MIMEImage),
    (b'audio content', 'audio/mp3', MIMEAudio),
    (b'binary content', 'application/pdf', MIMEBase),
])
def test_build_file_part(email_sender, file_content, content_type, expected_mime_class):
    """Test _build_file_part with different file types"""
    test_file = "test_file.txt"

    with patch('mimetypes.guess_type', return_value=(content_type, None)), \
            patch('builtins.open', mock_open(read_data=file_content)):
        result = email_sender._build_file_part(test_file)

        assert isinstance(result, expected_mime_class)
        assert result['Content-Disposition'] == f'attachment; filename="{test_file}"'


def test_create_message(email_sender):
    """Test _create_message method with different media types"""
    receiver_email = "receiver@example.com"
    file_path = "test.jpg"
    
    test_cases = [
        ("picture", "Picture Attachment"),
        ("video", "Video Attachment"),
        ("boomerang", "Boomerang Attachment")
    ]

    for media_type, expected_subject in test_cases:
        with patch.object(email_sender, '_build_file_part') as mock_build_part:
            mock_attachment = MIMEBase('application', 'octet-stream')
            mock_build_part.return_value = mock_attachment

            result = email_sender._create_message(receiver_email, file_path, media_type)

            assert isinstance(result, dict)
            assert 'raw' in result
            assert isinstance(result['raw'], str)
            
            # Decode the raw message to verify subject
            decoded = base64.urlsafe_b64decode(result['raw'].encode()).decode()
            assert f'Subject: {expected_subject}' in decoded
            
            mock_build_part.assert_called_once_with(file_path)


def test_send_message(email_sender, mock_service):
    """Test _send_message method"""
    test_message = {'raw': 'test_content'}

    email_sender._send_message(mock_service, test_message)

    mock_service.users().messages().send.assert_called_once_with(
        userId="me",
        body=test_message
    )


def test_send_email_success(email_sender, mock_credentials, mock_service):
    """Test successful email sending with different media types"""
    receiver_email = "receiver@example.com"
    file_path = "test.jpg"
    media_type = "video"

    with patch('config.configuration.service_build', return_value=mock_service), \
            patch.object(email_sender, '_create_message') as mock_create_message, \
            patch.object(email_sender, '_send_message') as mock_send_message:
        mock_message = {'raw': 'test_content'}
        mock_create_message.return_value = mock_message

        result = email_sender.send_email(mock_credentials, receiver_email, file_path, media_type)

        assert result == mock_message
        mock_create_message.assert_called_once_with(receiver_email, file_path, media_type)
        mock_send_message.assert_called_once_with(mock_service, mock_message)
        email_sender.logger.info.assert_called_once()


def test_send_email_failure(email_sender, mock_credentials):
    """Test email sending with HTTP error"""
    receiver_email = "receiver@example.com"
    file_path = "test.jpg"

    with patch('config.configuration.service_build', side_effect=HttpError(Mock(status=500), b'Error')):
        result = email_sender.send_email(mock_credentials, receiver_email, file_path)

        assert result is None
        email_sender.logger.error.assert_called_once()


def test_build_file_part_unknown_type(email_sender):
    """Test _build_file_part with unknown file type"""
    test_file = "test_file.xyz"
    test_content = b'test content'

    with patch('mimetypes.guess_type', return_value=(None, None)), \
            patch('builtins.open', mock_open(read_data=test_content)):
        result = email_sender._build_file_part(test_file)

        assert isinstance(result, MIMEBase)
        assert result.get_content_type() == 'application/octet-stream'
        assert result['Content-Disposition'] == f'attachment; filename="{test_file}"'


def test_build_file_part_with_encoding(email_sender):
    """Test _build_file_part with file that has encoding"""
    test_file = "test_file.gz"
    test_content = b'test content'

    with patch('mimetypes.guess_type', return_value=('application/gzip', 'gzip')), \
            patch('builtins.open', mock_open(read_data=test_content)):
        result = email_sender._build_file_part(test_file)

        assert isinstance(result, MIMEBase)
        assert result.get_content_type() == 'application/octet-stream'
