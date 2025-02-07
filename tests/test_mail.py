import unittest
from unittest.mock import patch, Mock, mock_open
import os
import base64
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.errors import HttpError
import logging
from mail import EmailSender

class TestEmailSender(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('test_logger')
        self.email_sender = EmailSender(self.logger)
        self.receiver_email = "test@example.com"
        self.test_file_path = "test_image.jpg"
        
    @patch('mail.config.service_build')
    def test_send_email_success(self, mock_service_build):
        # Setup mock service
        mock_service = Mock()
        mock_service_build.return_value = mock_service
        mock_service.users().messages().send().execute.return_value = {'id': '123'}
        
        # Test successful email sending
        result = self.email_sender.send_email(
            creds=Mock(),
            receiver_email=self.receiver_email,
            file_path=self.test_file_path
        )
        
        self.assertIsNotNone(result)
        mock_service.users().messages().send.assert_called_once()

    @patch('mail.config.service_build')
    def test_send_email_failure(self, mock_service_build):
        # Setup mock service to raise HttpError
        mock_service = Mock()
        mock_service_build.return_value = mock_service
        mock_service.users().messages().send.side_effect = HttpError(
            resp=Mock(status=500), content=b'Error'
        )
        
        # Test failed email sending
        result = self.email_sender.send_email(
            creds=Mock(),
            receiver_email=self.receiver_email,
            file_path=self.test_file_path
        )
        
        self.assertIsNone(result)

    @patch('builtins.open', new_callable=mock_open, read_data=b'test_image_data')
    def test_build_file_part_image(self, mock_file):
        # Test building MIME part for image file
        result = self.email_sender._build_file_part('test.jpg')
        
        self.assertIsInstance(result, MIMEImage)
        self.assertEqual(result.get_filename(), 'test.jpg')
        mock_file.assert_called_once_with('test.jpg', 'rb')

    @patch('builtins.open', new_callable=mock_open, read_data=b'test_text_data')
    def test_build_file_part_text(self, mock_file):
        # Test building MIME part for text file
        result = self.email_sender._build_file_part('test.txt')
        
        self.assertIsInstance(result, MIMEText)
        self.assertEqual(result.get_filename(), 'test.txt')
        mock_file.assert_called_once_with('test.txt', 'rb')

    def test_create_message(self):
        # Test message creation
        with patch.object(EmailSender, '_build_file_part') as mock_build_part:
            mock_build_part.return_value = MIMEText('test attachment')
            
            message = self.email_sender._create_message(
                self.receiver_email,
                self.test_file_path
            )
            
            self.assertIn('raw', message)
            # Decode the raw message to verify contents
            decoded = base64.urlsafe_b64decode(message['raw'].encode()).decode()
            self.assertIn(self.receiver_email, decoded)
            self.assertIn(self.email_sender.subject, decoded)
            self.assertIn(self.email_sender.body, decoded)

    @patch('mail.config.service_build')
    def test_send_message(self, mock_service_build):
        # Test the send_message static method
        mock_service = Mock()
        mock_message = {'raw': 'test_message'}
        
        EmailSender._send_message(mock_service, mock_message)
        
        mock_service.users().messages().send.assert_called_once_with(
            userId="me",
            body=mock_message
        )

if __name__ == '__main__':
    unittest.main()
