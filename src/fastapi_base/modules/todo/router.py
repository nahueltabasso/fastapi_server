from typing import Annotated

from fastapi import APIRouter, Query, status

from fastapi_base.modules.todo.dependencies import TodoServiceDep
from fastapi_base.modules.todo.schemas import TodoCreateDTO, TodoFilterDTO, TodoReadDTO
from fastapi_base.shared.schemas import PageDTO

router = APIRouter(prefix="/todo", tags=["todo"])


@router.get("/search", status_code=status.HTTP_200_OK)
async def search(
    service: TodoServiceDep,
    todoFilterDTO: Annotated[TodoFilterDTO, Query()],
) -> PageDTO[TodoReadDTO]:
    return await service.search(todoFilterDTO)


@router.get("", status_code=status.HTTP_200_OK)
async def find_all(service: TodoServiceDep):
    return await service.find_all()


@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
async def get_by_id(service: TodoServiceDep, todo_id: int):
    return await service.get_by_id(todo_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create(service: TodoServiceDep, todoDTO: TodoCreateDTO):
    return await service.create(todoDTO)


@router.patch("/{todo_id}", status_code=status.HTTP_200_OK)
async def update(service: TodoServiceDep, todo_id: int, todoDTO: TodoCreateDTO):
    return await service.update(todo_id, todoDTO)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(service: TodoServiceDep, todo_id: int):
    return await service.delete(todo_id)


@router.delete("/soft/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete(service: TodoServiceDep, todo_id: int):
    return await service.soft_delete(todo_id)
