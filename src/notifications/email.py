import asyncio
import smtplib
from email.mime.text import MIMEText
from config.settings import settings


def _send_sync(to: str, subject: str, body: str) -> bool:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user
    msg["To"] = to
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception:
        return False


async def send_email(to: str, subject: str, body: str) -> bool:
    """Envía email vía SMTP Outlook. Ejecuta en thread pool para no bloquear el event loop."""
    return await asyncio.to_thread(_send_sync, to, subject, body)
