from contextvars import ContextVar
from dataclasses import dataclass
from typing import Self

import structlog
from fastapi import Request

# Who made the current request. Complete by get_principal
current_user: ContextVar[str | None] = ContextVar("current_user", default=None)


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Request data for the current HTTP request"""

    ip: str | None
    user_agent: str | None
    request_id: str | None

    @classmethod
    def from_request(cls, request: Request) -> Self:
        return cls(
            ip=request.client.host if request.client else None,
            user_agent=(request.headers.get("user-agent") or "")[:255],
            request_id=structlog.contextvars.get_contextvars().get("request_id"),
        )
