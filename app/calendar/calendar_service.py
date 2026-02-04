from googleapiclient.discovery import build
from datetime import timedelta, datetime
import pytz 

class MeetingConflictError(Exception):
    pass

def get_calendar_service(credentials):
    return build("calendar", "v3", credentials=credentials)

def check_availability(service, start_dt, end_dt):
    """
    Usa events().list para buscar colisiones reales.
    Devuelve el TÍTULO del primer evento en conflicto si está ocupado.
    Devuelve None si está libre.
    """
    # Definir zona horaria local (Madrid)
    madrid_tz = pytz.timezone('Europe/Madrid')
    
    # Normalizar fechas
    if start_dt.tzinfo is None:
        start_dt = madrid_tz.localize(start_dt)
    else:
        start_dt = start_dt.astimezone(madrid_tz)
        
    if end_dt.tzinfo is None:
        end_dt = madrid_tz.localize(end_dt)
    else:
        end_dt = end_dt.astimezone(madrid_tz)

    time_min = start_dt.isoformat()
    time_max = end_dt.isoformat()

    print(f"🕵️ CHECKING CONFLICTS: {time_min} -> {time_max}")

    # Consultar eventos
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])

    for event in events:
        
        if event.get('transparency') == 'transparent':
            continue
            
        print(f"⚠️ CONFLICTO ENCONTRADO: {event['summary']}")
        
        return event['summary'] 

    return None 

def create_meeting(
    credentials,
    title: str,
    start_datetime, 
    duration_minutes: int,
    attendees: list[str]
):
    service = get_calendar_service(credentials)

    madrid_tz = pytz.timezone('Europe/Madrid')
    if start_datetime.tzinfo is None:
        start_datetime = madrid_tz.localize(start_datetime)
    
    end_datetime = start_datetime + timedelta(minutes=duration_minutes)

    # 1. VERIFICAR CONFLICTOS
    # Ahora conflict_event tendrá el nombre de la reunión 
    conflict_event_title = check_availability(service, start_datetime, end_datetime)
    
    if conflict_event_title:
        raise MeetingConflictError(f"Agenda ocupada: Coincide con '{conflict_event_title}'")

    # 2. CREAR EL EVENTO
    event_body = {
        "summary": title,
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": "Europe/Madrid",
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": "Europe/Madrid",
        },
    }

    if attendees:
        event_body["attendees"] = [{"email": email} for email in attendees]

    created_event = service.events().insert(
        calendarId="primary",
        body=event_body
    ).execute()