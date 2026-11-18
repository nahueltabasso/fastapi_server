from typing import Annotated

from fastapi import Depends

from fastapi_base.api.deps import SessionDep, get_session_revoker
from fastapi_base.modules.users.repository import (
    RoleRepository,
    UserRepository,
    UserRoleRepository,
)
from fastapi_base.modules.users.service import SessionRevoker, UserService


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
