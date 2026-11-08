from collections.abc import Sequence
from enum import Enum
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from fastapi_base.shared.schemas import PageDTO
from fastapi_base.shared.service import BaseService

AnyService = BaseService[Any, Any, Any, Any, Any]


logger = structlog.get_logger(__name__)


def build_base_router(
    *,
    prefix: str,
    tags: list[str | Enum],
    service_dep: Any,
    create_schema: type[BaseModel],
    update_schema: type[BaseModel],
    filter_schema: type[BaseModel],
    read_schema: type[BaseModel],
    dependencies: Sequence[Any] = (),
) -> APIRouter:
    """Basic Router for CRUD operations."""
    router = APIRouter(
        prefix=prefix,
        tags=tags,
        dependencies=dependencies,
    )

    @router.get(
        "/search", response_model=PageDTO[read_schema], status_code=status.HTTP_200_OK
    )
    async def search(
        filterDTO: Annotated[filter_schema, Query()],  # type: ignore[valid-type]
        base_service: service_dep,  # type: ignore[valid-type]
    ) -> PageDTO[read_schema]:  # type: ignore
        logger.info("Searching with filters", filters=filterDTO)
        return await base_service.search(filters=filterDTO)

    @router.get(
        "", response_model=Sequence[read_schema], status_code=status.HTTP_200_OK
    )
    async def get_all(
        service: service_dep,  # type: ignore
    ) -> Sequence[read_schema]:  # type: ignore
        logger.info("Enter to get_all()")
        return await service.find_all()

    @router.get(
        "/{item_id}", response_model=read_schema, status_code=status.HTTP_200_OK
    )
    async def get_one(
        item_id: int,
        service: service_dep,  # type: ignore
    ) -> read_schema:  # type: ignore
        logger.info("Enter to get_one()", item_id=item_id)
        return await service.get_by_id(item_id)

    @router.post("", response_model=read_schema, status_code=status.HTTP_201_CREATED)
    async def create(
        payload: create_schema,  # type: ignore
        service: service_dep,  # type: ignore
    ) -> read_schema:  # type: ignore
        logger.info("Enter to create()", payload=payload)
        return await service.create(payload)

    @router.patch(
        "/{item_id}", response_model=read_schema, status_code=status.HTTP_200_OK
    )
    async def update(
        item_id: int,
        payload: update_schema,  # type: ignore
        service: service_dep,  # type: ignore
    ) -> read_schema:  # type: ignore
        logger.info("Enter to update()", item_id=item_id, payload=payload)
        return await service.update(item_id, payload)

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete(
        item_id: int,
        service: service_dep,  # type: ignore
    ) -> None:
        logger.info("Enter to delete()", item_id=item_id)
        await service.delete(item_id)

    @router.delete("/soft/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def soft_delete(
        item_id: int,
        service: service_dep,  # type: ignore
    ) -> None:
        logger.info("Enter to soft_delete()", item_id=item_id)
        await service.soft_delete(item_id)

    return router
