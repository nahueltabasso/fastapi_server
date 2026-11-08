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
