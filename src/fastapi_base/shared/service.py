from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode
from fastapi_base.database.base import BaseEntity
from fastapi_base.shared.repository import BaseRepository
from fastapi_base.shared.schemas import BaseFilterDTO, PageDTO


class BaseService[
    ModelT: BaseEntity,
    CreateT: BaseModel,
    UpdateT: BaseModel,
    ReadT: BaseModel,
    FilterT: BaseFilterDTO,
]:
    """CRUD service with common operations for a given model."""

    read_schema: type[ReadT]
    entity_name: str = "Resource"

    def __init__(
        self, session: AsyncSession, repository: BaseRepository[ModelT, FilterT]
    ) -> None:
        self.session = session
        self.repository = repository

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        try:
            yield
            await self.session.commit()
        except IntegrityError, StaleDataError:
            await self.session.rollback()
            raise BusinessLogicError(
                message="Database error", error_code=ErrorCode.DB_ERROR
            )
        except Exception:
            await self.session.rollback()
            raise

    def build_entity(self, data: CreateT) -> ModelT:
        """Build an entity instance from the provided data."""
        return self.repository.model(**data.model_dump())

    async def get_entity_or_fail(self, entity_id: int) -> ModelT:
        """Retrieve an entity by its ID or raise an error if not found."""
        entity = await self.repository.get_by_id(entity_id)
        if not entity:
            raise BusinessLogicError(
                message=f"{self.entity_name} with ID {entity_id} not found",
                error_code=ErrorCode.NOT_FOUND,
            )
        return entity

    async def create(self, data: CreateT) -> ReadT:
        """Create a new resource based on the provided data."""
        async with self.transaction():
            entity = await self.repository.save(self.build_entity(data))
        return self.read_schema.model_validate(entity)

    async def find_all(self) -> Sequence[ReadT]:
        """Retrieve all resources that are not soft-deleted."""
        entities = await self.repository.find_all()
        return [self.read_schema.model_validate(entity) for entity in entities]

    async def get_by_id(self, entity_id: int) -> ReadT:
        """Retrieve a resource by its ID."""
        entity = await self.get_entity_or_fail(entity_id)
        return self.read_schema.model_validate(entity)

    async def delete(self, entity_id: int) -> None:
        """Delete a resource by its ID."""
        async with self.transaction():
            entity = await self.get_entity_or_fail(entity_id)
            await self.repository.delete(entity)

    async def soft_delete(self, entity_id: int) -> None:
        """Logic delete a resource by its ID."""
        async with self.transaction():
            entity = await self.get_entity_or_fail(entity_id)
            await self.repository.soft_delete(entity)

    async def search(self, filters: FilterT) -> PageDTO[ReadT]:
        """Search for resources based on the provided filter criteria."""
        items, total = await self.repository.get_page(filters=filters)
        return PageDTO(
            items=[self.read_schema.model_validate(item) for item in items],
            total=total,
            limit=filters.limit,
            offset=filters.offset,
        )

    async def update(self, entity_id: int, data: UpdateT) -> ReadT:
        """Update a resource by its ID."""
        async with self.transaction():
            entity = await self.get_entity_or_fail(entity_id)
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, key, value)
            entity = await self.repository.save(entity)
        return self.read_schema.model_validate(entity)
