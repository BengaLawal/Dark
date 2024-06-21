import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = "config/.credentials.json"
TOKEN_FILE = f"{os.path.expanduser('~')}/.token.json"  # saves token file in home dir


def login():
    """
    The function `user_authentication` checks if the user has valid credentials, and if not, it prompts
    the user to log in and saves the credentials for future use.
    :return: a service object that can be used to interact with the gmail API.
    """
    creds = check_if_token_exist()

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        save_token(creds, TOKEN_FILE)
    print("Successfully logged in.")
    return creds


def save_token(creds, path):
    """
    The function `save_token()` save the token for the next run
    """
    with open(path, 'w') as token:
        token.write(creds.to_json())


def service_build(creds):
    """
  The function `service_build` builds and returns a gmail service object using the provided
  credentials.

  :param creds: The `creds` parameter is the credentials object that is used to authenticate and
  authorize the application to access the gmail API. It contains the necessary information
  such as the client ID, client secret, and access token
  :return: the service object that is built using the 'gmail' API and the provided credentials.
  """
    return build('gmail', 'v1', credentials=creds)


def check_if_token_exist():
    """
  The file token.json stores the user's access and refresh tokens, and is
  created automatically when the authorization flow completes for the first time.
  :return: credentials if the file exists
  """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        return creds
    else:
        return creds
