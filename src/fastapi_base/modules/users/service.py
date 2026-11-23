from typing import Protocol

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode
from fastapi_base.core.security.principal import Principal
from fastapi_base.modules.users.models import User, UserRole
from fastapi_base.modules.users.repository import (
    RoleRepository,
    UserRepository,
    UserRoleRepository,
)
from fastapi_base.modules.users.schemas import (
    AssignRoleDTO,
    MeDTO,
    UserFilterDTO,
    UserReadDTO,
    UserUpdateDTO,
)
from fastapi_base.shared.schemas import PageDTO
from fastapi_base.shared.transaction import TransactionalService

logger = structlog.get_logger()


class SessionRevoker(Protocol):
    async def end_all(self, user_id: int) -> None: ...


class UserService(TransactionalService):
    def __init__(
        self,
        session: AsyncSession,
        *,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        user_role_repository: UserRoleRepository,
        revoker: SessionRevoker,
    ) -> None:
        super().__init__(session)
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.user_role_repository = user_role_repository
        self.revoker = revoker

    async def get_me(self, principal: Principal) -> MeDTO:
        logger.info("Enter to get_me()")
        user: User = await self._get_or_fail(user_id=principal.user_id)
        return MeDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            has_password=bool(user.password),
            permissions=sorted(principal.permissions),
        )

    async def update_me(self, principal: Principal, dataDTO: UserUpdateDTO) -> MeDTO:
        logger.info("Enter to update_me()")
        user: User = await self._get_or_fail(user_id=principal.user_id)
        async with self.transaction():
            for field, value in dataDTO.model_dump(exclude_unset=True).items():
                setattr(user, field, value)
            await self.user_repository.save(user)
            return await self.get_me(principal)

    async def search(self, filterDTO: UserFilterDTO) -> PageDTO[UserReadDTO]:
        logger.info("Enter to search()")
        items, total = await self.user_repository.get_page(filters=filterDTO)
        return PageDTO(
            items=[UserReadDTO.model_validate(item) for item in items],
            total=total,
            limit=filterDTO.limit,
            offset=filterDTO.offset,
        )

    async def assign_role(self, user_id: int, assignRoleDTO: AssignRoleDTO) -> None:
        logger.info("Enter to assign_role()")
        async with self.transaction():
            user: User = await self._get_or_fail(user_id=user_id)
            role = await self.role_repository.find_by_role(role=assignRoleDTO.role)
            if role is None:
                raise BusinessLogicError(
                    message=f"Role {assignRoleDTO.role} not found",
                    error_code=ErrorCode.NOT_FOUND,
                )

            if (
                await self.user_role_repository.get_assigment(
                    user_id=user.id, role_id=role.id
                )
                is None
            ):
                await self.user_role_repository.save(
                    UserRole(user_id=user.id, role_id=role.id)
                )

    async def remove_role(self, user_id: int, role_name: str) -> None:
        logger.info("Enter to remove_role()")
        async with self.transaction():
            user: User = await self._get_or_fail(user_id=user_id)
            role = await self.role_repository.find_by_role(role=role_name)
            if role is None:
                raise BusinessLogicError(
                    message=f"Role {role_name} not found",
                    error_code=ErrorCode.NOT_FOUND,
                )
            user_role = await self.user_role_repository.get_assigment(
                user_id=user.id, role_id=role.id
            )
            if user_role is not None:
                await self.user_role_repository.delete(user_role)

    async def deactivate_user(self, user_id: int) -> None:
        logger.info("Enter to deactivate_user()")
        async with self.transaction():
            user: User = await self._get_or_fail(user_id=user_id)
            user.is_active = False
            await self.user_repository.save(user)
            await self.revoker.end_all(user.id)

    async def _get_or_fail(self, user_id: int) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise BusinessLogicError(
                message=f"User with id {user_id} not found",
                error_code=ErrorCode.NOT_FOUND,
            )
        return user
