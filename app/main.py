from fastapi import FastAPI, Request, HTTPException # <--- AÑADIDO HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import os
from app.auth.google_auth import get_credentials, OAuthRedirect
from dotenv import load_dotenv

load_dotenv()

# =========================
# CONFIGURACIÓN URLS (LOCAL vs PROD)
# =========================
# Definimos dónde está el frontend. En local es localhost, en prod es Vercel.
# Esto lee la variable que pusimos en Render. Si no existe, usa localhost.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

# =========================
# AUTH / GOOGLE
# =========================
from app.auth.google_auth import (
    get_gmail_service,
    get_credentials,
    is_logged_in,
    TOKEN_PATH,
    exchange_code_for_token
)

# =========================
# GMAIL
# =========================
from app.gmail.gmail_service import (
    get_last_messages,
    get_message,
    get_message_body,
    extract_email_metadata,
)
from app.gmail.gmail_send_service import send_email_reply
from app.gmail.gmail_label_service import (
    archive_and_label_message,
    get_labels, 
    trash_message,
    add_label_to_message
)

# =========================
# IA
# =========================
from app.ai.email_analysis_service import analyze_email_structured

# =========================
# CALENDAR
# =========================

from app.calendar.calendar_service import create_meeting, MeetingConflictError 

# =========================
# FASTAPI SETUP
# =========================
app = FastAPI(title="Gmail AI Agent")

# Forzar login en cada arranque 
if os.path.exists(TOKEN_PATH):
    try:
        os.remove(TOKEN_PATH)
    except:
        pass

# =========================
# CORS (React)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        FRONTEND_URL,              # Permitimos la URL de Vercel
        FRONTEND_URL.rstrip("/")   # Por si acaso (sin barra al final)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# MODELOS
# =========================
class AnalyzeRequest(BaseModel):
    email_body: str


class ReplyRequest(BaseModel):
    message_id: str
    reply_text: str


class ArchiveRequest(BaseModel):
    message_id: str
    label_name: str = "AI-Handled"


class MeetingRequest(BaseModel):
    title: str
    start_datetime: str  
    duration_minutes: int = 60
    attendees: list[str] = []
    
class LabelRequest(BaseModel):
    label_name: str

# =========================
# BASIC ROUTES
# =========================
@app.get("/")
def root():
    return RedirectResponse(FRONTEND_URL)


@app.get("/login")
def login():
    if is_logged_in():
        return RedirectResponse(FRONTEND_URL)

    try:
        get_credentials()
    except OAuthRedirect as e:
        return RedirectResponse(e.url)

    return RedirectResponse(FRONTEND_URL)


@app.get("/logout")
def logout():
    if os.path.exists(TOKEN_PATH):
        try:
            os.remove(TOKEN_PATH)
        except:
            pass
    # CAMBIO: Devolvemos un JSON simple en lugar de una redirección
    return {"status": "logged_out"}


@app.get("/oauth2callback")
def oauth2callback(request: Request):
    exchange_code_for_token(str(request.url))
    return RedirectResponse(FRONTEND_URL)


# =========================
# GMAIL LABELS
# =========================
@app.get("/gmail/labels")
def gmail_labels():
    service = get_gmail_service()
    return get_labels(service)

# =========================
# EMAILS (CON LABEL)
# =========================
@app.get("/emails")
def read_emails(label: str = "INBOX"):
    """
    label:
    - INBOX
    - SENT
    - DRAFT
    - o cualquier labelId de Gmail
    """
    service = get_gmail_service()
    messages = get_last_messages(service, label_id=label)

    emails = []

    for msg in messages:
        full_msg = get_message(service, msg["id"])
        body = get_message_body(full_msg)
        meta = extract_email_metadata(full_msg)

        label_ids = full_msg.get("labelIds", [])
        unread = "UNREAD" in label_ids

        emails.append({
            "id": msg["id"],
            "from": meta["from"],
            "subject": meta["subject"],
            "snippet": full_msg.get("snippet"),
            "body": body,
            "unread": unread,
            "labels": full_msg.get("labelIds", []),
        })

    return emails



# =========================
# ANALYZE EMAIL BY ID
# =========================
@app.post("/emails/{message_id}/analyze")
def analyze_email_by_id(message_id: str):
    service = get_gmail_service()

    message = get_message(service, message_id)
    body = get_message_body(message)

    if not body or body.strip() == "":
        return {
            "error": "EMPTY_EMAIL_BODY",
            "message": "No se pudo extraer el cuerpo del correo",
        }

    return analyze_email_structured(body)

# =========================
# REPLY EMAIL
# =========================
@app.post("/reply")
def reply_to_email(data: ReplyRequest):
    service = get_gmail_service()
    original_message = get_message(service, data.message_id)
    meta = extract_email_metadata(original_message)

    send_email_reply(
        service=service,
        to_email=meta["from"],
        subject=f"Re: {meta['subject']}",
        body=data.reply_text,
        thread_id=meta["threadId"],
    )

    return {"status": "reply sent"}

# =========================
# ARCHIVE / LABEL
# =========================
@app.post("/archive")
def archive_email(data: ArchiveRequest):
    service = get_gmail_service()

    archive_and_label_message(
        service=service,
        message_id=data.message_id,
        label_name=data.label_name,
    )

    return {"status": "email archived and labeled"}

# =========================
# CALENDAR (ENDPOINT ACTUALIZADO)
# =========================
@app.post("/calendar/meeting")
def create_calendar_meeting(data: MeetingRequest):
    credentials = get_credentials()

    try:
        start_dt = datetime.fromisoformat(data.start_datetime.replace("Z", "+00:00"))
    except ValueError:
        start_dt = datetime.fromisoformat(data.start_datetime)

    try:
        link = create_meeting(
            credentials=credentials,
            title=data.title,
            start_datetime=start_dt,
            duration_minutes=data.duration_minutes,
            attendees=data.attendees,
        )

        return {
            "status": "meeting created",
            "calendar_link": link,
        }

    except MeetingConflictError as e:
        # AQUÍ CAPTURAMOS EL CONFLICTO Y DEVOLVEMOS 409
        print(f"Conflicto de agenda: {e}")
        raise HTTPException(status_code=409, detail=str(e))
        
    except Exception as e:
        print(f"Error creando evento: {e}")
        raise HTTPException(status_code=500, detail="Error interno creando el evento")


# =========================
# USER / AUTH UTILS
# =========================
@app.get("/auth/status")
def auth_status():
    return {"logged_in": is_logged_in()}

@app.post("/emails/{message_id}/mark-read")
def mark_email_as_read(message_id: str):
    service = get_gmail_service()

    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "removeLabelIds": ["UNREAD"]
        }
    ).execute()

    return {"status": "marked as read"}

@app.get("/auth/user")
def get_user_info():
    service = get_gmail_service()

    profile = service.users().getProfile(userId="me").execute()

    return {
        "email": profile.get("emailAddress")
    }


@app.post("/emails/{message_id}/trash")
def trash_email_endpoint(message_id: str):
    service = get_gmail_service()
    trash_message(service, message_id)
    return {"status": "trashed"}


@app.post("/emails/{message_id}/label")
def add_label_to_email_json(message_id: str, data: LabelRequest):
    service = get_gmail_service()

    add_label_to_message(
        service=service,
        message_id=message_id,
        label_name=data.label_name,
    )

    return {"status": "label added"}


@app.post("/emails/{message_id}/add-label")
def add_label_to_email_query(message_id: str, label: str):
    try:
        service = get_gmail_service()
        add_label_to_message(service, message_id, label)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))