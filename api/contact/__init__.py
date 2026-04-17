import html
import json
import logging
import os
import re

import azure.functions as func
from azure.communication.email import EmailClient

logger = logging.getLogger(__name__)

MAX_SHORT_LEN = 200
MAX_MESSAGE_LEN = 5000


def main(req: func.HttpRequest) -> func.HttpResponse:
    # Only allow POST
    if req.method != "POST":
        return func.HttpResponse(status_code=405)

    # Parse body
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()
    message = (body.get("message") or "").strip()
    page = (body.get("page") or "general").strip()

    # Validate required fields
    if not name or not email or not message:
        return func.HttpResponse(
            json.dumps({"error": "Name, email, and message are required"}),
            status_code=400,
            mimetype="application/json",
        )

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return func.HttpResponse(
            json.dumps({"error": "Invalid email address"}),
            status_code=400,
            mimetype="application/json",
        )

    if (
        len(name) > MAX_SHORT_LEN
        or len(email) > MAX_SHORT_LEN
        or len(page) > MAX_SHORT_LEN
        or len(message) > MAX_MESSAGE_LEN
    ):
        return func.HttpResponse(
            json.dumps({"error": "Input too long"}),
            status_code=400,
            mimetype="application/json",
        )

    name_h = html.escape(name, quote=True)
    email_h = html.escape(email, quote=True)
    page_h = html.escape(page, quote=True)
    message_h = html.escape(message, quote=True).replace("\n", "<br>")

    # Send email via Azure Communication Services
    connection_string = os.environ.get("ACS_CONNECTION_STRING")
    sender = os.environ.get("ACS_EMAIL_FROM")
    recipient = os.environ.get("CONTACT_EMAIL_TO")

    if not connection_string or not sender or not recipient:
        logger.error("Missing ACS configuration")
        return func.HttpResponse(
            json.dumps({"error": "Server configuration error"}),
            status_code=500,
            mimetype="application/json",
        )

    try:
        client = EmailClient.from_connection_string(connection_string)
        email_message = {
            "senderAddress": sender,
            "content": {
                "subject": f"ZipTriage Contact — {page} — {name}",
                "plainText": (
                    f"Name: {name}\n"
                    f"Email: {email}\n"
                    f"Page: {page}\n\n"
                    f"Message:\n{message}"
                ),
                "html": (
                    f"<h2>New contact from ZipTriage website</h2>"
                    f"<p><strong>Name:</strong> {name_h}</p>"
                    f"<p><strong>Email:</strong> <a href=\"mailto:{email_h}\">{email_h}</a></p>"
                    f"<p><strong>Page:</strong> {page_h}</p>"
                    f"<hr>"
                    f"<p>{message_h}</p>"
                ),
            },
            "recipients": {
                "to": [{"address": recipient}],
            },
        }

        poller = client.begin_send(email_message)
        result = poller.result()
        logger.info(f"Contact email sent, message_id={result.message_id}")

        return func.HttpResponse(
            json.dumps({"success": True}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.exception("Failed to send contact email")
        return func.HttpResponse(
            json.dumps({"error": "Failed to send message. Please try again later."}),
            status_code=500,
            mimetype="application/json",
        )
