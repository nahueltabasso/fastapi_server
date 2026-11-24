from collections.abc import Sequence

import structlog
from fastapi import Depends

from fastapi_base.api.deps import require
from fastapi_base.modules.todo.dependencies import TodoServiceDep
from fastapi_base.modules.todo.permissions import TodoPermission
from fastapi_base.modules.todo.schemas import (
    TodoCreateDTO,
    TodoFilterDTO,
    TodoReadDTO,
    TodoUpdateDTO,
)
from fastapi_base.shared.router import build_base_router

logger = structlog.get_logger(__name__)


router = build_base_router(
    prefix="/todo",
    tags=["todo"],
    service_dep=TodoServiceDep,
    create_schema=TodoCreateDTO,
    update_schema=TodoUpdateDTO,
    filter_schema=TodoFilterDTO,
    read_schema=TodoReadDTO,
    read_permission=TodoPermission.READ,
    write_permission=TodoPermission.WRITE,
)


@router.get(
    "/filter/{state}",
    response_model=list[TodoReadDTO],
    status_code=200,
    dependencies=[Depends(require(TodoPermission.READ))],
)
async def get_by_state(
    state: str,
    service: TodoServiceDep,
) -> Sequence[TodoReadDTO]:
    logger.info("Enter to get_by_state()", state=state)
    return await service.get_todos_by_state(state)
