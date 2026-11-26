import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated, Protocol

import jwt
from fastapi import Request
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode
from fastapi_base.core.security.principal import Principal
from fastapi_base.core.security.tokens import decode_access_token
from fastapi_base.database.session import SessionDep


class PrincipalLoader(Protocol):
    """Build the Principal for a valid token."""

    async def __call__(
        self, session: AsyncSession, user_id: int, session_id: uuid.UUID
    ) -> Principal | None: ...


bearer = HTTPBearer(auto_error=False)


async def get_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: SessionDep,
) -> Principal:
    """Verify the token and load the current user as a Principal in the current context."""
    if credentials is None:
        raise BusinessLogicError(
            message="Missing credentials", error_code=ErrorCode.UNAUTHORIZED
        )

    try:
        claims = decode_access_token(token=credentials.credentials)
    except jwt.InvalidTokenError as exc:
        raise BusinessLogicError(
            message="Invalid token", error_code=ErrorCode.UNAUTHORIZED
        ) from exc

    loader: PrincipalLoader = request.app.state.principal_loader
    principal = await loader(
        session=session, user_id=int(claims["sub"]), session_id=uuid.UUID(claims["sid"])
    )
    if principal is None:
        raise BusinessLogicError(
            message="Invalid or revoke session", error_code=ErrorCode.UNAUTHORIZED
        )
    return principal


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
