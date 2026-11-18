from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.modules.users.models import Role, RolePermission

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "user": {"todos:read", "todos:write"},
    "admin": {"todos:read", "todos:write", "users:read", "users:write", "users:manage"},
}


async def seed_roles(session: AsyncSession) -> None:
    for role_name, permissions in ROLE_PERMISSIONS.items():
        await session.execute(
            insert(Role)
            .values(role=role_name)
            .on_conflict_do_nothing(
                index_elements=["role"], index_where=text("NOT deleted")
            )
        )
        role_id = await session.scalar(select(Role.id).where(Role.role == role_name))
        for permission in permissions:
            await session.execute(
                insert(RolePermission)
                .values(role_id=role_id, permission=permission)
                .on_conflict_do_nothing(
                    index_elements=["role_id", "permission"],
                    index_where=text("NOT deleted"),
                )
            )
    await session.commit()
