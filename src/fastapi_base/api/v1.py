from fastapi import APIRouter

from fastapi_base.core.config import get_settings
from fastapi_base.modules.todo.router import router as todo_router

settings = get_settings()

api_router = APIRouter(prefix=settings.api_prefix)

api_router.include_router(todo_router)
