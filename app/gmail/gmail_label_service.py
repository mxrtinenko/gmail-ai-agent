def get_or_create_label(service, label_name):
    labels = service.users().labels().list(userId="me").execute().get("labels", [])

    for label in labels:
        if label["name"] == label_name:
            return label["id"]

    label_body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show"
    }

    created_label = service.users().labels().create(
        userId="me",
        body=label_body
    ).execute()

    return created_label["id"]


def archive_and_label_message(service, message_id, label_name):
    label_id = get_or_create_label(service, label_name)

    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "addLabelIds": [label_id],
            "removeLabelIds": ["INBOX"]
        }
    ).execute()

def get_labels(service):
    """
    Devuelve todas las labels de Gmail (system + user)
    """
    results = service.users().labels().list(
        userId="me"
    ).execute()

    labels = results.get("labels", [])

    return [
        {
            "id": label["id"],
            "name": label["name"],
            "type": label["type"],
        }
        for label in labels
    ]

def trash_message(service, message_id):
    service.users().messages().trash(
        userId="me",
        id=message_id
    ).execute()

def add_label_to_message(service, message_id: str, label_name: str):
    """
    Añade una label a un mensaje de Gmail.
    Crea la label si no existe.
    NO elimina INBOX.
    """

    # Obtener labels existentes
    labels_response = service.users().labels().list(userId="me").execute()
    labels = labels_response.get("labels", [])

    label_id = None
    for label in labels:
        if label["name"].lower() == label_name.lower():
            label_id = label["id"]
            break

    # Crear la label si no existe
    if not label_id:
        new_label = service.users().labels().create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        ).execute()
        label_id = new_label["id"]

    # Añadir la label al mensaje
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "addLabelIds": [label_id],
        },
    ).execute()

