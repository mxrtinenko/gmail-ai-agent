import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Permitir HTTP solo en local
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]

# === CONFIGURACIÓN INTELIGENTE (LOCAL VS NUBE) ===

# 1. Archivo de Secretos:
# En Render lo buscamos en /etc/secrets/ (definido por variable de entorno)
# En Local lo buscamos en app/auth/client_secret.json
CLIENT_SECRETS_FILE = os.environ.get("GOOGLE_CLIENT_SECRETS_FILE", "app/auth/client_secret.json")

# 2. Token de Sesión:
# Lo guardamos siempre en app/auth/token.json (Render permite escritura temporal)
TOKEN_PATH = "app/auth/token.json"

# 3. URL de Redirección (Callback):
# Si estamos en Render, usamos su URL externa. Si no, localhost.
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL') 
if RENDER_EXTERNAL_URL:
    REDIRECT_URI = f"{RENDER_EXTERNAL_URL}/oauth2callback"
else:
    REDIRECT_URI = "http://localhost:8001/oauth2callback"

# =================================================


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


def get_credentials():
    if not os.path.exists(TOKEN_PATH):
        raise OAuthRedirect(_build_auth_url())

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())
            return creds
        except Exception:
             raise OAuthRedirect(_build_auth_url())

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

    # Aseguramos que el directorio exista antes de guardar
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    
    with open(TOKEN_PATH, "w") as token:
        token.write(creds.to_json())


def get_gmail_service():
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)