import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import os

class EmailSender:
    def __init__(self):
        self.sender_email = "flawben111@gmail.com"
        self.password = os.environ.get("EMAIL_PASSWORD")
        self.subject = 'Picture Attachment'
        self.body = "Enjoy your photos!\nDon't forget to share using #RUSHCLAREMONT"

    def send_email(self, receiver_email, path, function):
        """
        handles sending the email with attachment
        :param receiver_email: the customers email
        :param path: path to the picture that needs to be sent
        """
        # SMTP server settings
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587  # or the appropriate port number
        smtp_username = self.sender_email
        smtp_password = self.password

        # Compose the email
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = receiver_email
        msg['Subject'] = self.subject

        if function == "picture":
            # Attach the picture
            with open(path, 'rb') as picture_file:
                picture_data = picture_file.read()
                picture_mime = MIMEImage(picture_data, name='picture.jpg')
                msg.attach(picture_mime)
        elif function == "video":
            # Attach the video
            with open(path, 'rb') as video_file:
                video_data = video_file.read()
                video_mime = MIMEBase('application', 'octet-stream')
                video_mime.set_payload(video_data)
                encoders.encode_base64(video_mime)
                video_mime.add_header('Content-Disposition', 'attachment', filename=os.path.basename(path))
                msg.attach(video_mime)

        # Add the body message
        body = MIMEText(self.body)
        msg.attach(body)

        # Send the email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            print("Email sent successfully!")
        except Exception as e:
            print("An error occurred while sending the email:", str(e))
