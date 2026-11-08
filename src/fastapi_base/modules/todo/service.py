from collections.abc import Sequence

from fastapi_base.modules.todo.models import Todo
from fastapi_base.modules.todo.repository import TodoRepository
from fastapi_base.modules.todo.schemas import TodoCreateDTO, TodoFilterDTO, TodoReadDTO
from fastapi_base.shared.service import BaseService


class TodoService(
    BaseService[Todo, TodoCreateDTO, TodoCreateDTO, TodoReadDTO, TodoFilterDTO]
):
    read_schema = TodoReadDTO
    entity_name = "Todo"
    repository: TodoRepository

    async def get_todos_by_state(self, state: str) -> Sequence[TodoReadDTO]:
        entities = await self.repository.get_by_state(state)
        return [self.read_schema.model_validate(entity) for entity in entities]
