from fastapi_base.modules.users.models import Role, User, UserRole
from fastapi_base.modules.users.schemas import (
    RoleFilterDTO,
    UserFilterDTO,
    UserRoleFilterDTO,
)
from fastapi_base.shared.repository import BaseRepository


class UserRepository(BaseRepository[User, UserFilterDTO]):
    model = User


class RoleRepository(BaseRepository[Role, RoleFilterDTO]):
    model = Role


class UserRoleRepository(BaseRepository[UserRole, UserRoleFilterDTO]):
    model = UserRole
