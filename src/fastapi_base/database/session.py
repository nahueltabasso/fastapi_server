from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from fastapi_base.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    str(settings.database_url),
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,
    pool_recycle=1800,
)


SessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_session() -> AsyncIterator[AsyncIterator]:
    """A session per request. After exit the session is closed."""
    async with SessionFactory() as session:
        yield session  # type: ignore
