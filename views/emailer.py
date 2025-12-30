"""
Email Sender Utility
--------------------

This module provides an async-friendly wrapper for sending emails
with attachments (such as generated PDF reports).

You may later upgrade it to use:
- SMTP with SSL/TLS
- SendGrid API
- Mailgun API
- AWS SES

For now it uses Python's built-in smtplib for simplicity.
"""

import smtplib
import ssl
from email.message import EmailMessage
from typing import List, Optional
import logging

from app.config.settings import settings

logger = logging.getLogger("tanmiya.views.emailer")


def _build_email(
    subject: str,
    body: str,
    to: List[str],
    pdf_bytes: Optional[bytes] = None,
    pdf_filename: str = "report.pdf"
) -> EmailMessage:
    """Internal helper to construct email with optional PDF attachment."""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = ", ".join(to)
    msg.set_content(body)

    if pdf_bytes:
        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=pdf_filename,
        )

    return msg


async def send_email(
    to: List[str],
    subject: str,
    body: str,
    pdf_bytes: Optional[bytes] = None,
    pdf_filename: str = "report.pdf",
) -> bool:
    """
    Send an email with or without PDF attachment.
    This function is sync internally but wrapped for async compatibility.
    """

    msg = _build_email(subject, body, to, pdf_bytes, pdf_filename)

    try:
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {to}")
        return True

    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return False
