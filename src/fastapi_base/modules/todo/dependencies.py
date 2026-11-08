from typing import Annotated

from fastapi import Depends

from fastapi_base.api.deps import SessionDep
from fastapi_base.modules.todo.repository import TodoRepository
from fastapi_base.modules.todo.service import TodoService


def get_todo_service(session: SessionDep) -> TodoService:
    return TodoService(session=session, repository=TodoRepository(session=session))


TodoServiceDep = Annotated[TodoService, Depends(get_todo_service)]
