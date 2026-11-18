from fastapi_base.core.config import Settings
from fastapi_base.core.email import EmailSender


class AuthMailer:
    def __init__(self, sender: EmailSender, settings: Settings) -> None:
        self._sender = sender
        self._settings = settings
        self._frontend_url = settings.frontend_url

    async def send_verification_email(self, to: str, token: str) -> None:
        """Send a verification email to the specified recipient."""
        url = f"{self._frontend_url}/verify-email#token={token}"
        hours = self._settings.email_verification_ttl_hours
        await self._sender.send(
            to,
            "Confirm your account",
            f"To confirm your account, please click the following link: {url}\n\n"
            f"This link will expire in {hours} hours.",
        )

    async def send_password_reset_email(self, to: str, token: str) -> None:
        """Send a password reset email to the specified recipient."""
        url = f"{self._frontend_url}/reset-password#token={token}"
        minutes = self._settings.password_reset_ttl_minutes
        await self._sender.send(
            to,
            "Reset your password",
            f"To reset your password, please click the following link: {url}\n\n"
            f"This link will expire in {minutes} minutes.",
        )

    async def send_password_changed_email(self, to: str) -> None:
        """Send a password changed notification email to the specified recipient."""
        await self._sender.send(
            to,
            "Your password has been changed",
            "Your password has been successfully changed. If you did not perform this action, please contact support immediately.",
        )
