import os
import base64
import mimetypes
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.errors import HttpError
from config import configuration as config
from dotenv import load_dotenv
from email import encoders

load_dotenv()

class EmailSender:
    """A class to send emails with attachments using Gmail API."""

    def __init__(self):
        self.sender = os.getenv("SENDER_EMAIL")
        self.subject = 'Picture Attachment'
        self.body = "Enjoy your photos!\nDon't forget to share using #RUSHCLAREMONT"

    def send_email(self, creds, receiver_email, file_path):
        """
        Sends an email with an attachment.
        Args:
            creds: The credentials for authenticating with the Gmail API.
            receiver_email: The recipient's email address.
            file_path: The path to the file to be attached.

        Returns:
            The message object if the email was sent successfully, None otherwise.
        """
        try:
            service = config.service_build(creds)
            message = self._create_message(receiver_email, file_path)
            self._send_message(service, message)
            print("Email sent successfully")
        except HttpError as error:
            print(f"Failed to send email: {error}")
            message = None
        return message

    def _create_message(self, receiver_email, path):
        """
        Creates an email message with an attachment.
        Args:
            receiver_email: The recipient's email address.
            path: The path to the file to be attached.

        Returns:
            The email message in raw format encoded in base64 URL-safe.
        """
        message = MIMEMultipart()
        message["To"] = receiver_email
        message["From"] = self.sender
        message["Subject"] = self.subject
        message.attach(MIMEText(self.body))
        attachment = self._build_file_part(path)
        message.attach(attachment)
        return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

    @staticmethod
    def _send_message(service, message):
        """
        Sends an email message using the Gmail API.
        Args:
            service: The Gmail API service object.
            message: The email message to be sent.
        """
        # pylint: disable=E1101
        service.users().messages().send(userId="me", body=message).execute()

    @staticmethod
    def _build_file_part(file):
        """Creates a MIME part for a file.
        Args:
          file: The path to the file to be attached.
        Returns:
          A MIME part that can be attached to a message.
        """
        content_type, encoding = mimetypes.guess_type(file)

        if content_type is None or encoding is not None:
            content_type = "application/octet-stream"
        main_type, sub_type = content_type.split("/", 1)
        if main_type == "text":
            with open(file, "rb") as data:
                msg = MIMEText(data.read().decode("utf-8"), _subtype=sub_type)
        elif main_type == "image":
            with open(file, "rb") as data:
                msg = MIMEImage(data.read(), _subtype=sub_type)
        elif main_type == "audio":
            with open(file, "rb")as data:
                msg = MIMEAudio(data.read(), _subtype=sub_type)
        else:
            with open(file, "rb") as data:
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(data.read())
                # encoders.encode_base64(msg)
        filename = os.path.basename(file)
        msg.add_header("Content-Disposition", "attachment", filename=filename)
        return msg
