import os
import pickle
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

# === CONFIGURACIÓN ===
CLIENT_SECRETS_FILE = os.environ.get("GOOGLE_CLIENT_SECRETS_FILE", "app/auth/client_secret.json")
TOKEN_PATH = "app/auth/token.json"
FLOW_STORAGE_PATH = "app/auth/flow_storage.pickle"

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

    raise OAuthRedirect(_build_auth_url())


def _build_auth_url():
    """Genera la URL y guarda state y code_verifier."""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    # CORRECCIÓN 1: Capturamos 'state' aquí (antes era _)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    
    # Guardamos los datos necesarios para reconstruir el flow luego
    save_data = {
        'code_verifier': flow.code_verifier,
        'state': state  # Usamos la variable capturada arriba
    }
    
    try:
        os.makedirs(os.path.dirname(FLOW_STORAGE_PATH), exist_ok=True)
        with open(FLOW_STORAGE_PATH, 'wb') as f:
            pickle.dump(save_data, f)
    except Exception as e:
        print(f"Error guardando datos temporales: {e}")

    return auth_url


def exchange_code_for_token(callback_url: str):
    """Reconstruye el Flow y canjea el código."""
    
    save_data = {}
    
    # 1. Recuperamos datos
    if os.path.exists(FLOW_STORAGE_PATH):
        try:
            with open(FLOW_STORAGE_PATH, 'rb') as f:
                save_data = pickle.load(f)
        except Exception as e:
            print(f"Error cargando datos temporales: {e}")

    # 2. CORRECCIÓN 2: Pasamos el 'state' al constructor
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=save_data.get('state') # <--- IMPORTANTE
    )

    # 3. Inyectamos el code_verifier
    if 'code_verifier' in save_data:
        flow.code_verifier = save_data['code_verifier']
    else:
        print("⚠️ ALERTA: Login sin code_verifier (puede fallar).")

    # 4. Canjeamos
    flow.fetch_token(authorization_response=callback_url)

    creds = flow.credentials
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w") as token:
        token.write(creds.to_json())
        
    # Limpieza
    if os.path.exists(FLOW_STORAGE_PATH):
        try:
            os.remove(FLOW_STORAGE_PATH)
        except:
            pass

def get_gmail_service():
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)