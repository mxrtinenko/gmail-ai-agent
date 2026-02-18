import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]

CLIENT_SECRETS_FILE = "app/auth/client_secret.json"
TOKEN_PATH = "app/auth/token.json"
REDIRECT_URI = "http://localhost:8001/oauth2callback"


class OAuthRedirect(Exception):
    def __init__(self, url: str):
        self.url = url



def is_logged_in():
    if not os.path.exists(TOKEN_PATH):
        return False

    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        return creds.valid or (creds.expired and creds.refresh_token)
    except Exception:
        return False






from google.auth.transport.requests import Request


def get_credentials():
    if not os.path.exists(TOKEN_PATH):
        raise OAuthRedirect(_build_auth_url())

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
        return creds

    if creds.valid:
        return creds

    # Si hay token pero NO es válido → forzar login
    raise OAuthRedirect(_build_auth_url())

def _build_auth_url():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    return auth_url




def exchange_code_for_token(callback_url: str):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    flow.fetch_token(authorization_response=callback_url)

    creds = flow.credentials

    with open(TOKEN_PATH, "w") as token:
        token.write(creds.to_json())

from googleapiclient.discovery import build


def get_gmail_service():
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)