import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.core.security.tokens import hash_opaque_token, new_opaque_token
from fastapi_base.modules.auth.models import ActionToken, RefreshToken, TokenPurpose


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, refresh_token: RefreshToken) -> None:
        self.session.add(refresh_token)
        await self.session.flush()

    async def find_by_token(self, token: str) -> RefreshToken | None:
        result = await self.session.scalars(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token)
            .with_for_update()
        )
        return result.first()

    async def revoke_family(self, family_id: uuid.UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None)
            )
            .values(revoked_at=datetime.now())
        )

    async def revoke_all(
        self, user_id: int, now: datetime, *, keep: uuid.UUID | None = None
    ) -> None:
        stmt = update(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        if keep is not None:
            stmt = stmt.where(RefreshToken.id != keep)
        stmt = stmt.values(revoked_at=now)
        await self.session.execute(stmt)

    async def is_session_active(self, family_id: uuid.UUID, now: datetime) -> bool:
        """True while the session is neither revoked nor expired"""
        stmt = select(
            exists().where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
        )
        return bool(await self.session.scalar(stmt))


class ActionTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def issue(self, user_id: int, purpose: TokenPurpose, ttl: timedelta) -> str:
        now = datetime.now(UTC)
        await self.session.execute(
            update(ActionToken)
            .where(
                ActionToken.user_id == user_id,
                ActionToken.purpose == purpose,
                ActionToken.used_at.is_(None),
            )
            .values(used_at=now)
        )
        raw, token_hash = new_opaque_token()
        self.session.add(
            ActionToken(
                user_id=user_id,
                purpose=purpose,
                token_hash=token_hash,
                expires_at=now + ttl,
            )
        )
        await self.session.flush()
        return raw

    async def consume(self, raw: str, purpose: TokenPurpose) -> ActionToken | None:
        now = datetime.now(UTC)
        stmt = (
            update(ActionToken)
            .where(
                ActionToken.token_hash == hash_opaque_token(raw),
                ActionToken.purpose == purpose,
                ActionToken.used_at.is_(None),
                ActionToken.expires_at > now,
            )
            .values(used_at=now)
            .returning(ActionToken)
        )
        return await self.session.scalar(stmt)
