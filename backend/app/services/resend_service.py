import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    email_id: str | None = None,
) -> str | None:
    """
    Send an email via Gmail SMTP using an app password.
    Returns a pseudo email ID on success, None on failure.
    """
    return await asyncio.to_thread(_send_sync, to_email, subject, body, email_id)


def _send_sync(
    to_email: str,
    subject: str,
    body: str,
    email_id: str | None,
) -> str | None:
    msg = MIMEMultipart()
    msg["From"] = settings.gmail_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.gmail_user, settings.gmail_app_password)
            server.sendmail(settings.gmail_user, to_email, msg.as_string())
        return email_id or "sent"
    except smtplib.SMTPAuthenticationError:
        print("[Gmail] Authentication failed — check GMAIL_USER and GMAIL_APP_PASSWORD in .env")
        return None
    except Exception as e:
        print(f"[Gmail] Failed to send to {to_email}: {e}")
        return None
