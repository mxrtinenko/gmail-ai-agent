import os
import pickle  # <--- IMPORT NECESARIO PARA GUARDAR MEMORIA
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
CLIENT_SECRETS_FILE = os.environ.get("GOOGLE_CLIENT_SECRETS_FILE", "app/auth/client_secret.json")

# 2. Token de Sesión:
TOKEN_PATH = "app/auth/token.json"

# 3. Archivo Temporal de Flujo (EL ARREGLO):
# Aquí guardaremos el "estado" intermedio del login
FLOW_PICKLE_PATH = "app/auth/flow_storage.pickle"

# 4. URL de Redirección (Callback):
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
    """Genera la URL y GUARDA el estado en un archivo pickle."""
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
    
    # --- ARREGLO INICIO ---
    # Guardamos el objeto 'flow' entero (que tiene el code_verifier dentro)
    try:
        os.makedirs(os.path.dirname(FLOW_PICKLE_PATH), exist_ok=True)
        with open(FLOW_PICKLE_PATH, 'wb') as f:
            pickle.dump(flow, f)
    except Exception as e:
        print(f"Error guardando flow pickle: {e}")
    # --- ARREGLO FIN ---

    return auth_url


def exchange_code_for_token(callback_url: str):
    """Recupera el estado guardado y canjea el código."""
    
    flow = None
    
    # --- ARREGLO INICIO ---
    # Intentamos recuperar el flow guardado (que tiene el secreto)
    if os.path.exists(FLOW_PICKLE_PATH):
        try:
            with open(FLOW_PICKLE_PATH, 'rb') as f:
                flow = pickle.load(f)
        except Exception as e:
            print(f"Error cargando flow pickle: {e}")
    # --- ARREGLO FIN ---

    # Si por lo que sea falló la carga, creamos uno nuevo (aunque esto fallará por el verifier)
    if not flow:
        print("⚠️ Advertencia: No se encontró pickle, creando flujo nuevo (puede fallar 'invalid_grant')")
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )

    # Canjeamos el token
    flow.fetch_token(authorization_response=callback_url)

    creds = flow.credentials

    # Aseguramos que el directorio exista antes de guardar
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    
    with open(TOKEN_PATH, "w") as token:
        token.write(creds.to_json())
        
    # Limpieza: Borramos el archivo temporal
    if os.path.exists(FLOW_PICKLE_PATH):
        os.remove(FLOW_PICKLE_PATH)


def get_gmail_service():
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)