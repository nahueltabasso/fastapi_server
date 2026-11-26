import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.core.context import current_user
from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode
from fastapi_base.core.security.principal import Principal
from fastapi_base.core.security.tokens import decode_access_token
from fastapi_base.database.session import get_session
from fastapi_base.modules.auth.repository import RefreshTokenRepository
from fastapi_base.modules.auth.sessions import SessionService
from fastapi_base.modules.users.repository import UserRepository
from fastapi_base.modules.users.service import SessionRevoker

SessionDep = Annotated[AsyncSession, Depends(get_session)]

bearer = HTTPBearer(auto_error=False)


async def get_principal(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    session: SessionDep,
) -> Principal:
    """Verify the token and load the current user as a Principal in the current context."""
    if credentials is None:
        raise BusinessLogicError(
            message="Missing credentialas", error_code=ErrorCode.UNAUTHORIZED
        )
    try:
        claims = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError as exc:
        raise BusinessLogicError(
            message="Invalid token", error_code=ErrorCode.UNAUTHORIZED
        ) from exc
    session_id = uuid.UUID(claims["sid"])
    refresh_token_repository = RefreshTokenRepository(session)
    if not await refresh_token_repository.is_session_active(
        session_id, now=datetime.now(UTC)
    ):
        raise BusinessLogicError(
            message="Session Revoked", error_code=ErrorCode.UNAUTHORIZED
        )
    user_repository = UserRepository(session)
    user = await user_repository.get_by_id(int(claims["sub"]))
    if user is None or not user.is_active:
        raise BusinessLogicError(
            message="Invalid token", error_code=ErrorCode.UNAUTHORIZED
        )
    current_user.set(str(user.id))
    return Principal(
        user_id=user.id,
        session_id=uuid.UUID(claims["sid"]),
        permissions=await user_repository.get_permissions(user.id),
    )


CurrentPrincipal = Annotated[Principal, Depends(get_principal)]


def require(*permissions: str) -> Callable[..., Awaitable[Principal]]:
    """Require the specified permissions for the current principal."""

    async def checker(principal: CurrentPrincipal) -> Principal:
        if not set(permissions) <= principal.permissions:
            raise BusinessLogicError(
                message="Insufficient permissions", error_code=ErrorCode.UNAUTHORIZED
            )
        return principal

    return checker


def get_session_revoker(session: SessionDep) -> SessionRevoker:
    return SessionService(RefreshTokenRepository(session))
