from email.message import EmailMessage
from typing import Protocol

import aiosmtplib
import structlog

from fastapi_base.core.config import Settings

logger = structlog.get_logger(__name__)


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email using SMTP."""
        logger.info("Sending email", to=to, subject=subject)
        message = EmailMessage()
        message["From"] = self._settings.mail_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        password = self._settings.smtp_password
        if password is None:
            logger.error("SMTP password is not set")
            return
        try:
            await aiosmtplib.send(
                message,
                hostname=self._settings.smtp_host,
                port=self._settings.smtp_port,
                username=self._settings.smtp_username,
                password=password.get_secret_value(),
                start_tls=self._settings.smtp_start_tls,
                timeout=10,
            )
        except aiosmtplib.SMTPException, OSError:
            logger.exception(
                "email_send_failed", subject=subject, to_domain=to.rsplit("@", 1)[-1]
            )
