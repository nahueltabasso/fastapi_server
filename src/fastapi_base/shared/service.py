from collections.abc import Sequence

import structlog
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode
from fastapi_base.database.base import BaseEntity
from fastapi_base.shared.repository import BaseRepository
from fastapi_base.shared.schemas import BaseFilterDTO, PageDTO
from fastapi_base.shared.transaction import TransactionalService

logger = structlog.get_logger(__name__)


class BaseService[
    ModelT: BaseEntity,
    CreateT: BaseModel,
    UpdateT: BaseModel,
    ReadT: BaseModel,
    FilterT: BaseFilterDTO,
](TransactionalService):
    """CRUD service with common operations for a given model."""

    read_schema: type[ReadT]
    entity_name: str = "Resource"

    def __init__(
        self, session: AsyncSession, repository: BaseRepository[ModelT, FilterT]
    ) -> None:
        super().__init__(session)
        self.repository = repository

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
        logger.info("Enter to create()")
        async with self.transaction():
            entity = await self.repository.save(self.build_entity(data))
        return self.read_schema.model_validate(entity)

    async def find_all(self) -> Sequence[ReadT]:
        """Retrieve all resources that are not soft-deleted."""
        logger.info("Enter to find_all()")
        entities = await self.repository.find_all()
        return [self.read_schema.model_validate(entity) for entity in entities]

    async def get_by_id(self, entity_id: int) -> ReadT:
        """Retrieve a resource by its ID."""
        logger.info("Enter to get_by_id()")
        entity = await self.get_entity_or_fail(entity_id)
        return self.read_schema.model_validate(entity)

    async def delete(self, entity_id: int) -> None:
        """Delete a resource by its ID."""
        logger.info("Enter to delete()")
        async with self.transaction():
            entity = await self.get_entity_or_fail(entity_id)
            await self.repository.delete(entity)

    async def soft_delete(self, entity_id: int) -> None:
        """Logic delete a resource by its ID."""
        logger.info("Enter to soft_delete()")
        async with self.transaction():
            entity = await self.get_entity_or_fail(entity_id)
            await self.repository.soft_delete(entity)

    async def search(self, filters: FilterT) -> PageDTO[ReadT]:
        """Search for resources based on the provided filter criteria."""
        logger.info("Enter to search()", filters=filters)
        items, total = await self.repository.get_page(filters=filters)
        return PageDTO(
            items=[self.read_schema.model_validate(item) for item in items],
            total=total,
            limit=filters.limit,
            offset=filters.offset,
        )

    async def update(self, entity_id: int, data: UpdateT) -> ReadT:
        """Update a resource by its ID."""
        logger.info("Enter to update()")
        async with self.transaction():
            entity = await self.get_entity_or_fail(entity_id)
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(entity, key, value)
            entity = await self.repository.save(entity)
        return self.read_schema.model_validate(entity)
