import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.core.security.principal import Principal
from fastapi_base.modules.auth.repository import RefreshTokenRepository
from fastapi_base.modules.auth.sessions import SessionService
from fastapi_base.modules.users.repository import UserRepository
from fastapi_base.modules.users.service import SessionRevoker


async def load_principal(
    session: AsyncSession, user_id: int, session_id: uuid.UUID
) -> Principal | None:
    """Load the Principal for the given user and session IDs."""
    refresh_token_repository = RefreshTokenRepository(session=session)
    if not await refresh_token_repository.is_session_active(
        family_id=session_id, now=datetime.now(UTC)
    ):
        return None
    user_repository = UserRepository(session=session)
    user = await user_repository.get_by_id(entity_id=user_id)
    if user is None or not user.is_active:
        return None
    return Principal(
        user_id=user.id,
        session_id=session_id,
        permissions=await user_repository.get_permissions(user_id=user.id),
    )


def session_revoker_factory(session: AsyncSession) -> SessionRevoker:
    return SessionService(RefreshTokenRepository(session=session))
