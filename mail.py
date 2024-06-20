import base64
import mimetypes
from email.message import EmailMessage
from googleapiclient.errors import HttpError
from config import configuration as config


class EmailSender:
    def __init__(self):
        self.sender = "olawal023@student.wethinkcode.co.za"
        self.subject = 'Picture Attachment'
        self.body = "Enjoy your photos!\nDon't forget to share using #RUSHCLAREMONT"

    def send_email(self, creds, receiver_email, path):
        """Create and insert a draft email with attachment.
         Print the returned draft's message and id.
        Returns: Draft object, including draft id and message metadata.
        """

        try:
            # create gmail api client
            service = config.service_build(creds)
            message = EmailMessage()

            # headers
            message["To"] = receiver_email
            message["From"] = self.sender
            message["Subject"] = self.subject

            # text
            message.set_content(self.body)

            # attachment
            attachment_filename = path
            # guessing the MIME type
            type_subtype, _ = mimetypes.guess_type(attachment_filename)
            maintype, subtype = type_subtype.split("/")

            with open(attachment_filename, "rb") as fp:
                attachment_data = fp.read()
            message.add_attachment(attachment_data, maintype, subtype)

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            create_message = {"raw": encoded_message}
            # pylint: disable=E1101
            message = (
                service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
            )
            print("Email sent successfully")
        except HttpError as error:
            print(f"An error occurred: {error}")
            message = None
        return message
