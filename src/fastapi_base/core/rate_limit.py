from collections.abc import Awaitable, Callable
from time import time
from typing import Protocol

from fastapi import Request
from redis.asyncio import Redis

from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode


class RateLimiter(Protocol):
    async def hit(self, key: str, limit: int, window_s: int) -> bool:
        """Count one hit for key. Return False when the limit is exceeded."""
        ...


class RedisRateLimiter:
    """Fixed window rate limiter using Redis."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def hit(self, key: str, limit: int, window_s: int) -> bool:
        async with self.redis.pipeline(transaction=True) as pipeline:
            pipeline.incr(key)
            pipeline.expire(key, window_s, nx=True)
            count, _ = await pipeline.execute()
        return int(count) <= limit


class InMemoryRateLimiter:
    """Only for local development and testing purposes."""

    def __init__(self) -> None:
        self.windows: dict[str, tuple[float, int]] = {}

    async def hit(self, key: str, limit: int, window_s: int) -> bool:
        now = time.monotonic()
        started, count = self.windows.get(key, (now, 0))
        if now - started >= window_s:
            started, count = now, 0
        self.windows[key] = (started, count + 1)
        return count + 1 <= limit


async def enforce(limiter: RateLimiter, key: str, limit: int, window_s: int) -> None:
    if not await limiter.hit(key, limit, window_s):
        raise BusinessLogicError(
            message="Too many requests", error_code=ErrorCode.RATE_LIMITED
        )


def get_rate_limiter(request: Request) -> RateLimiter:
    limiter: RateLimiter = request.app.state.rate_limiter
    return limiter


def rate_limit_by_ip(
    scope: str, *, limit: int, window_s: int
) -> Callable[[Request], Awaitable[None]]:
    """Dependency: at most ´limit´ calls per client IP every window_s seconds."""

    async def dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        await enforce(get_rate_limiter(request), f"rl:{scope}:ip:{ip}", limit, window_s)

    return dependency
