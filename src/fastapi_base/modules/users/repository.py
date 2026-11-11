from sqlalchemy import select

from fastapi_base.modules.users.models import (
    Role,
    RolePermission,
    User,
    UserIdentity,
    UserRole,
)
from fastapi_base.modules.users.schemas import (
    RoleFilterDTO,
    UserFilterDTO,
    UserRoleFilterDTO,
)
from fastapi_base.shared.repository import BaseRepository
from fastapi_base.shared.schemas import BaseFilterDTO


class UserRepository(BaseRepository[User, UserFilterDTO]):
    model = User

    async def find_by_email(self, email: str) -> User | None:
        return await self.session.scalar(self.base_query().where(User.email == email))

    async def find_by_username(self, username: str) -> User | None:
        return await self.session.scalar(
            self.base_query().where(User.username == username)
        )

    async def get_permissions(self, user_id: int) -> frozenset[str]:
        stmt = (
            select(RolePermission.permission)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                ~UserRole.deleted,
                ~Role.deleted,
                ~RolePermission.deleted,
            )
        )
        return frozenset((await self.session.scalars(stmt)).all())


class RoleRepository(BaseRepository[Role, RoleFilterDTO]):
    model = Role

    async def find_by_role(self, role: str) -> Role | None:
        return await self.session.scalar(self.base_query().where(Role.role == role))


class UserRoleRepository(BaseRepository[UserRole, UserRoleFilterDTO]):
    model = UserRole


class UserIdentityRepository(BaseRepository[UserIdentity, BaseFilterDTO]):
    model = UserIdentity

    async def get(self, provider: str, subject: str) -> UserIdentity | None:
        stmt = self.base_query().where(
            UserIdentity.provider == provider, UserIdentity.subject == subject
        )
        return await self.session.scalar(stmt)
