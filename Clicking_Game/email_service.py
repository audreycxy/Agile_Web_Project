"""
Email backend used by the signup verification flow.

This project uses Resend's HTTPS API as the only email delivery backend.
This matches the deployed Render environment, where outbound SMTP ports are
not used for verification emails.

`send_email` raises on failure. Callers should wrap it in try/except so a
transient email-delivery problem does not turn a successful account creation
into a 500 error page.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from flask import current_app


RESEND_API_URL = "https://api.resend.com/emails"
RESEND_DEFAULT_SENDER = "onboarding@resend.dev"


def send_email(subject, recipients, body):
    """Send a plain-text email through Resend."""
    resend_api_key = current_app.config.get("RESEND_API_KEY")

    if not resend_api_key:
        raise RuntimeError(
            "RESEND_API_KEY is not configured. Email verification requires Resend."
        )

    _send_via_resend(resend_api_key, subject, recipients, body)


def _send_via_resend(api_key, subject, recipients, body):
    """
    POST to Resend's HTTPS API. We use stdlib urllib so we do not need to
    pull in the `resend` SDK or `requests` as new dependencies.
    """
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
            "Accept": "application/json",
            "User-Agent": "ClickingGame/1.0 (+https://agile-web-project.onrender.com)",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Resend API returned HTTP {error.code} for sender={sender!r} "
            f"recipients={list(recipients)!r}: {error_body}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Resend API request failed for {list(recipients)!r}: {error}"
        ) from error
