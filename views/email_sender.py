# app/views/email_sender.py
"""
Email sender utility using aiosmtplib (async).
Used for sending English & Arabic PDFs after generation.
"""

import os
import aiosmtplib
from email.message import EmailMessage
from typing import List
from app.config.settings import settings


async def send_email(
    to: List[str],
    subject: str,
    body: str,
    attachments: List[str] = None,
):
    """
    Send email with attachments asynchronously.
    """
    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = ", ".join(to)
    message["Subject"] = subject
    message.set_content(body)

    # Attach files
    if attachments:
        for path in attachments:
            filename = os.path.basename(path)
            with open(path, "rb") as f:
                message.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="pdf",
                    filename=filename
                )

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASS,
        use_tls=True,
    )
