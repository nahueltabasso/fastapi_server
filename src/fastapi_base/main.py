from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_base.api import health
from fastapi_base.api.v1 import api_router
from fastapi_base.core.config import get_settings
from fastapi_base.core.error_handlers import register_exception_handlers
from fastapi_base.core.logging import RequestIdMiddleware, configure_logging
from fastapi_base.database.base import Base
from fastapi_base.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(json_logs=get_settings().json_logs)
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await app.state.http.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    is_prod = settings.env == "production"

    app = FastAPI(
        title=settings.project_name,
        lifespan=lifespan,
        docs_url="/docs" if not is_prod else None,
        redoc_url=None,
        openapi_url="/openapi.json" if not is_prod else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(api_router)

    return app


app = create_app()
