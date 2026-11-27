from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

import fastapi_base.database.events
import fastapi_base.database.models  # noqa: F401  (tables registration)
from fastapi_base.api import health
from fastapi_base.api.v1 import api_router
from fastapi_base.core.config import get_settings
from fastapi_base.core.error_handlers import register_exception_handlers
from fastapi_base.core.logging import RequestIdMiddleware, configure_logging
from fastapi_base.core.rate_limit import InMemoryRateLimiter, RedisRateLimiter

# from fastapi_base.database.base import Base
from fastapi_base.database.seed import seed_roles
from fastapi_base.database.session import Database
from fastapi_base.modules.auth.principal import load_principal, session_revoker_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(json_logs=settings.json_logs, level=settings.logging_level)
    redis = Redis.from_url(settings.redis_url) if settings.redis_url else None
    if redis is None and settings.env == "production":
        raise RuntimeError("APP_REDIS_URL is required in production")
    app.state.rate_limiter = (
        RedisRateLimiter(redis) if redis is not None else InMemoryRateLimiter()
    )
    db: Database = Database(settings)
    app.state.db = db
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
    # async with db.engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    async with db.sessionmaker() as session:
        await seed_roles(session)
    try:
        yield
    finally:
        await app.state.http.aclose()
        await app.state.db.dispose()
        if redis is not None:
            await redis.aclose()


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

    app.state.settings = settings
    app.state.principal_loader = load_principal
    app.state.session_revoker_factory = session_revoker_factory

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
