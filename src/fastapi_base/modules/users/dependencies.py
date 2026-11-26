from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.database.session import SessionDep
from fastapi_base.modules.users.repository import (
    RoleRepository,
    UserRepository,
    UserRoleRepository,
)
from fastapi_base.modules.users.service import SessionRevoker, UserService


def get_session_revoker(request: Request, session: SessionDep) -> SessionRevoker:
    factory: Callable[[AsyncSession], SessionRevoker] = (
        request.app.state.session_revoker_factory
    )
    return factory(session)


def get_user_service(
    session: SessionDep,
    revoker: Annotated[SessionRevoker, Depends(get_session_revoker)],
) -> UserService:
    return UserService(
        session,
        user_repository=UserRepository(session),
        role_repository=RoleRepository(session),
        user_role_repository=UserRoleRepository(session),
        revoker=revoker,
    )


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
