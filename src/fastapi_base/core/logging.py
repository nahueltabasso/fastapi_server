import logging
import logging.config
import re
import uuid

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from structlog.types import Processor

SHARED_PROCESSORS: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
]


def configure_logging(*, json_logs: bool, level: str = "INFO") -> None:
    renderer: list[Processor] = (
        [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
        if json_logs
        else [structlog.dev.ConsoleRenderer()]
    )

    # Process the events with Structlog and given to logging
    structlog.configure(
        processors=[
            *SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Formatting logging with dictConfig
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structlog": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "foreign_pre_chain": SHARED_PROCESSORS,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        *renderer,
                    ],
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "structlog",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {"handlers": ["console"], "level": level},
            "loggers": {
                "uvicorn": {
                    "handlers": ["console"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["console"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": level,
                    "propagate": False,
                },
                "sqlalchemy.engine": {"level": "INFO"},
            },
        }
    )


_VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")


class RequestIdMiddleware:
    """Middleware ASGI puro: pone X-Request-ID en la respuesta y en todos los logs de la request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        raw = dict(scope["headers"]).get(b"x-request-id", b"").decode("latin-1")
        request_id = raw if _VALID_REQUEST_ID.fullmatch(raw) else str(uuid.uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append(
                    (b"x-request-id", request_id.encode())
                )
            await send(message)

        await self.app(scope, receive, send_with_request_id)
