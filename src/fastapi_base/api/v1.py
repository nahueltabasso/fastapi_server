"""Agregador de routers de la API v1.

Cada módulo expone su propio `router` con su sub-prefijo (ej: "/todo") y acá se
montan todos bajo el prefijo global (`settings.api_prefix`).

Para sumar un módulo nuevo: importar su router y agregar un `include_router`.
"""

from fastapi import APIRouter

from fastapi_base.core.config import get_settings
from fastapi_base.modules.todo.router import router as todo_router

settings = get_settings()

api_router = APIRouter(prefix=settings.api_prefix)

api_router.include_router(todo_router)
