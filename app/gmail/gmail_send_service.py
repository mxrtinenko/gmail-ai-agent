import base64
from email.message import EmailMessage

def send_email_reply(service, to_email, subject, body, thread_id=None):
    message = EmailMessage()
    message.set_content(body)
    message["To"] = to_email
    message["Subject"] = subject

    if thread_id:
        message["In-Reply-To"] = thread_id
        message["References"] = thread_id

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    send_message = {
        "raw": encoded_message
    }

    if thread_id:
        send_message["threadId"] = thread_id

    service.users().messages().send(
        userId="me",
        body=send_message
    ).execute()
    
    # extrae los datos de destinatario, asunto y threadId
def extract_email_metadata(message):
    headers = message["payload"]["headers"]

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
