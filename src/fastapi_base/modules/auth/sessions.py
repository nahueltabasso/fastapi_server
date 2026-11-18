import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi_base.core.config import get_settings
from fastapi_base.core.context import RequestContext
from fastapi_base.core.security.tokens import (
    create_access_token,
    hash_opaque_token,
    new_opaque_token,
)
from fastapi_base.modules.auth.models import RefreshToken
from fastapi_base.modules.auth.repository import RefreshTokenRepository
from fastapi_base.modules.auth.schemas import ClientType

REUSE_GRACE = timedelta(seconds=10)


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_at: datetime
    client_type: ClientType


class SessionService:
    """Emite, rotates and revoke sessions."""

    def __init__(self, refresh_token_repository: RefreshTokenRepository) -> None:
        self.refresh_token_repository = refresh_token_repository

    async def start(
        self, user_id: int, client_type: ClientType, request_context: RequestContext
    ) -> TokenPair:
        now = datetime.now(UTC)
        family_expires_at = now + timedelta(days=get_settings().session_max_days)
        return await self._issue(
            user_id, uuid.uuid4(), family_expires_at, client_type, request_context, now
        )

    async def rotate(
        self, raw_token: str, request_context: RequestContext
    ) -> tuple[TokenPair | None, int | None]:
        """With reuse revoke the session."""
        now = datetime.now(UTC)
        token = await self.refresh_token_repository.find_by_token(
            hash_opaque_token(raw_token)
        )
        if token is None or token.revoked_at is not None:
            return None, None
        if token.used_at is not None:
            if now - token.used_at <= REUSE_GRACE:
                return None, None
            await self.refresh_token_repository.revoke_family(token.family_id)
            return None, token.user_id

        if token.expires_at <= now or token.family_expires_at <= now:
            return None, None
        token.used_at = now
        client_type: ClientType = "mobile" if token.client_type == "mobile" else "web"
        pair = await self._issue(
            token.user_id,
            token.family_id,
            token.family_expires_at,
            client_type,
            request_context,
            now,
        )
        return pair, None

    async def end(self, raw_token: str) -> int | None:
        """logout: revoke the session associated with the given token."""
        token = await self.refresh_token_repository.find_by_token(
            hash_opaque_token(raw_token)
        )
        if token is None:
            return None
        await self.refresh_token_repository.revoke_family(token.family_id)
        return token.user_id

    async def end_all(self, user_id: int, *, keep: uuid.UUID | None = None) -> None:
        """Revoke all sessions for the given user, optionally keeping one family."""
        await self.refresh_token_repository.revoke_all(
            user_id, datetime.now(UTC), keep=keep
        )

    async def _issue(
        self,
        user_id: int,
        family_id: uuid.UUID,
        family_expires_at: datetime,
        client_type: ClientType,
        request_context: RequestContext,
        now: datetime,
    ) -> TokenPair:
        raw, token_hash = new_opaque_token()
        ttl = timedelta(days=get_settings().refresh_token_ttl_days)
        expires_at = min(now + ttl, family_expires_at)
        await self.refresh_token_repository.save(
            RefreshToken(
                user_id=user_id,
                family_id=family_id,
                family_expires_at=family_expires_at,
                client_type=client_type,
                user_agent=request_context.user_agent,
                token_hash=token_hash,
                expires_at=expires_at,
                ip=request_context.ip,
            )
        )
        access_token, expires_in = create_access_token(user_id, family_id)
        return TokenPair(
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=raw,
            refresh_expires_at=expires_at,
            client_type=client_type,
        )
