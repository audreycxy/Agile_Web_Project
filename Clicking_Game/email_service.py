"""
Pluggable email backend used by the signup verification flow.

If RESEND_API_KEY is configured, send via Resend's HTTPS API. This works on
hosts like Render's free tier that block outbound SMTP (ports 25 / 465 /
587) at the network level.

Otherwise fall back to Flask-Mail SMTP, which is the simpler path for local
development against Gmail or any other SMTP server.

`send_verification_email` raises on failure. Callers should wrap it in
try/except so a transient email-delivery problem does not turn a successful
account creation into a 500 error page.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from flask import current_app
from flask_mail import Message

from Clicking_Game.extensions import mail


logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_DEFAULT_SENDER = "onboarding@resend.dev"


def send_email(subject, recipients, body):
    """Send a plain-text email. Backend depends on app config."""
    resend_api_key = current_app.config.get("RESEND_API_KEY")

    if resend_api_key:
        _send_via_resend(resend_api_key, subject, recipients, body)
    else:
        _send_via_smtp(subject, recipients, body)


def _send_via_resend(api_key, subject, recipients, body):
    """
    POST to Resend's HTTPS API. We use stdlib urllib so we do not need to
    pull in the `resend` SDK or `requests` as new dependencies.
    """
    # Resend rejects sends from arbitrary addresses; fall back to their
    # shared testing domain when the configured sender is not a Resend-
    # verified address. Operators can override either side by setting
    # MAIL_DEFAULT_SENDER and verifying that domain in their Resend dashboard.
    sender = (
        current_app.config.get("MAIL_DEFAULT_SENDER") or RESEND_DEFAULT_SENDER
    )

    payload = json.dumps(
        {
            "from": sender,
            "to": list(recipients),
            "subject": subject,
            "text": body,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        RESEND_API_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
    except urllib.error.HTTPError as error:
        # Resend returns useful JSON error bodies (e.g. invalid sender,
        # unverified domain, rate-limit hit). Log them so the operator can
        # diagnose without enabling Flask debug mode.
        error_body = error.read().decode("utf-8", errors="replace")
        logger.error(
            "Resend API returned %s for %s: %s",
            error.code,
            recipients,
            error_body,
        )
        raise
    except urllib.error.URLError as error:
        logger.error("Resend API request failed for %s: %s", recipients, error)
        raise


def _send_via_smtp(subject, recipients, body):
    """Send through Flask-Mail using the existing MAIL_* configuration."""
    message = Message(
        subject=subject,
        recipients=list(recipients),
        body=body,
    )
    mail.send(message)
