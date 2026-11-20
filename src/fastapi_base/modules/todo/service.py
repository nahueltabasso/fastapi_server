from collections.abc import Sequence

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode
from fastapi_base.core.security.principal import Principal
from fastapi_base.modules.todo.models import Todo
from fastapi_base.modules.todo.repository import TodoRepository
from fastapi_base.modules.todo.schemas import TodoCreateDTO, TodoFilterDTO, TodoReadDTO
from fastapi_base.shared.service import BaseService

logger = structlog.get_logger(__name__)


class TodoService(
    BaseService[Todo, TodoCreateDTO, TodoCreateDTO, TodoReadDTO, TodoFilterDTO]
):
    read_schema = TodoReadDTO
    entity_name = "Todo"
    repository: TodoRepository

    def __init__(
        self, repository: TodoRepository, session: AsyncSession, principal: Principal
    ):
        self.repository = repository
        self.session = session
        self.principal = principal

    async def get_todos_by_state(self, state: str) -> Sequence[TodoReadDTO]:
        logger.info("Enter to get_todos_by_state()", state=state)
        entities = await self.repository.get_by_state(state)
        return [self.read_schema.model_validate(entity) for entity in entities]

    async def create(self, dataDTO: TodoCreateDTO) -> TodoReadDTO:
        logger.info("Enter to create() hijo", dataDTO=dataDTO)

        if dataDTO.user_id != self.principal.user_id:
            raise BusinessLogicError(
                message="User ID does not match the principal's user ID",
                error_code=ErrorCode.UNAUTHORIZED,
            )
        async with self.transaction():
            todo = await self.repository.save(
                Todo(
                    user_id=dataDTO.user_id,
                    title=dataDTO.title,
                    state=dataDTO.state,
                )
            )
        return self.read_schema.model_validate(todo)
