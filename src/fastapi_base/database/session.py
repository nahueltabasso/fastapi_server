from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fastapi_base.core.config import Settings


class Database:
    """Engine + Session Factory."""

    def __init__(self, settings: Settings) -> None:
        self.engine = create_async_engine(
            str(settings.database_url),
            hide_parameters=True,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_pre_ping=True,
            pool_recycle=1800,
        )
        self.sessionmaker = async_sessionmaker(
            self.engine, expire_on_commit=False, autoflush=False
        )

    async def dispose(self) -> None:
        await self.engine.dispose()


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """A session per request. After exit the session is closed."""
    db: Database = request.app.state.db
    async with db.sessionmaker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
