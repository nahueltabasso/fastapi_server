from fastapi import APIRouter

from fastapi_base.core.config import get_settings
from fastapi_base.modules.auth.router import router as auth_router
from fastapi_base.modules.todo.router import router as todo_router
from fastapi_base.modules.users.router import router as users_router

settings = get_settings()

api_router = APIRouter(prefix=settings.api_prefix)

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(todo_router)
