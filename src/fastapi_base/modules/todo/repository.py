from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, select

from fastapi_base.modules.todo.models import Todo
from fastapi_base.modules.todo.schemas import TodoFilterDTO
from fastapi_base.shared.repository import BaseRepository


class TodoRepository(BaseRepository[Todo, TodoFilterDTO]):
    model = Todo

    async def get_by_state(self, state: str) -> Sequence[Todo]:
        result = await self.session.execute(select(Todo).where(Todo.state == state))
        return result.scalars().all()

    def apply_filter(
        self, stmt: Select[tuple[Any]], filter: TodoFilterDTO
    ) -> Select[tuple[Any]]:
        if filter.state is not None:
            stmt = stmt.where(Todo.state == filter.state)

        return stmt
