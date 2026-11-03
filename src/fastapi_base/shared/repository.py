from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode
from fastapi_base.database.base import BaseEntity
from fastapi_base.shared.schemas import BaseFilterDTO


class BaseRepository[ModelT: BaseEntity, FilterT: BaseFilterDTO]:
    """Basic repository with common CRUD operations."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def base_query(self) -> Select[Any]:
        """Starting point for every read: excludes soft-deleted rows."""
        return select(self.model).where(self.model.deleted.is_(False))

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        """Get an entity by its ID."""
        return await self.session.scalar(
            self.base_query().where(self.model.id == entity_id)
        )

    async def get_page(self, filters: FilterT) -> tuple[Sequence[ModelT], int]:
        """Get a page of entities with limit and offset."""
        stmt = self.apply_filter(self.base_query(), filters)
        total = await self.session.scalar(
            select(func.count()).select_from(stmt.subquery())
        )
        stmt = (
            self.apply_sort(stmt, filters.sort)
            .limit(filters.limit)
            .offset(filters.offset)
        )
        items = (await self.session.scalars(stmt)).all()
        return items, total or 0

    def apply_filter(self, stmt: Select[Any], filter: FilterT) -> Select[Any]:
        """Apply filtering to a query based on the provided filter DTO."""
        return stmt

    def apply_sort(self, stmt: Select[Any], sort: str) -> Select[Any]:
        """Apply sorting to a query based on the provided sort string."""
        field = sort.removeprefix("-")
        column = self.model.__table__.c.get(field)
        if column is None:
            raise BusinessLogicError("Column not found", ErrorCode.COLUMN_NOT_FOUND)
        order = column.desc() if sort.startswith("-") else column.asc()
        return stmt.order_by(order, self.model.id)

    async def save(self, entity: ModelT) -> ModelT:
        """Save an entity to the database."""
        self.session.add(entity)
        await self.session.flush()  # Execute INSERT and detect constraints violations
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Delete an entity from the database."""
        await self.session.delete(entity)
        await self.session.flush()

    async def soft_delete(self, entity: ModelT) -> None:
        """Soft delete an entity by setting its deleted flag to True."""
        entity.deleted = True
        self.session.add(entity)
        await self.session.flush()
