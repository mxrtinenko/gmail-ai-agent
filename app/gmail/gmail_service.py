import base64


def get_last_messages(service, label_id="INBOX", max_results=20):
    params = {
        "userId": "me",
        "maxResults": max_results,
    }

    SYSTEM_LABELS_USING_QUERY = {
        "SENT": "in:sent",
        "DRAFT": "in:drafts",
        "TRASH": "in:trash",
        "ALL_MAIL": "in:all",
    }

    if label_id in SYSTEM_LABELS_USING_QUERY:
        params["q"] = SYSTEM_LABELS_USING_QUERY[label_id]
    else:
        params["labelIds"] = [label_id]

    results = service.users().messages().list(**params).execute()
    return results.get("messages", [])



def get_message_body(message):
    """
    Extrae el body de un mensaje Gmail (text/plain o text/html)
    """
    payload = message.get("payload", {})
    body = ""

    def extract_from_part(part):
        data = part.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        return ""

    # Caso simple
    if payload.get("body", {}).get("data"):
        return extract_from_part(payload)

    # Multipart
    for part in payload.get("parts", []):
        mime = part.get("mimeType", "")

        if mime == "text/plain":
            return extract_from_part(part)

        if mime == "text/html" and not body:
            body = extract_from_part(part)

    return body


def _extract_body_from_parts(parts):
    for part in parts:
        mime_type = part.get("mimeType", "")

        # Caso texto plano
        if mime_type == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8")

        # Caso HTML (fallback)
        if mime_type == "text/html":
            data = part.get("body", {}).get("data")
            if data:
                html = base64.urlsafe_b64decode(data).decode("utf-8")
                return html  # luego podemos limpiarlo

        # Caso multipart (recursivo)
        if part.get("parts"):
            result = _extract_body_from_parts(part["parts"])
            if result:
                return result

    return ""


def get_message_body(message):
    payload = message.get("payload", {})

    # Caso simple
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode("utf-8")

    # Caso multipart
    parts = payload.get("parts", [])
    return _extract_body_from_parts(parts)


def extract_email_metadata(message):
    headers = message.get("payload", {}).get("headers", [])

    def get_header(name):
        for h in headers:
            if h["name"].lower() == name.lower():
                return h["value"]
        return ""

    return {
        "from": get_header("From"),
        "subject": get_header("Subject"),
        "threadId": message.get("threadId")
    }

def get_labels(service):
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])

    return [
        {
            "id": label["id"],
            "name": label["name"],
            "type": label["type"]
        }
        for label in labels
    ]

def get_message(service, message_id):
    """
    Obtiene un mensaje completo de Gmail por ID
    """
    return service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

