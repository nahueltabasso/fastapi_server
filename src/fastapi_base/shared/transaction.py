from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode

logger = structlog.get_logger(__name__)


class TransactionalService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        depth: int = self.session.info.get("tx_depth", 0)
        self.session.info["tx_depth"] = depth + 1
        try:
            yield
            if depth == 0:
                await self.session.commit()
        except (IntegrityError, StaleDataError) as e:
            await self.session.rollback()
            logger.warning("database conflict", error_type=type(e).__name__)
            raise BusinessLogicError(
                message="Database error", error_code=ErrorCode.DB_ERROR
            ) from e
        except Exception:
            if depth == 0:
                await self.session.rollback()
            raise
        finally:
            self.session.info["tx_depth"] = depth
