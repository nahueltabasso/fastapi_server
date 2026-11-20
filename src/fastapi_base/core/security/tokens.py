import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from fastapi_base.core.config import get_settings

ALGORITHM = "EdDSA"


def create_access_token(user_id: int, session_id: uuid.UUID) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(UTC)
    ttl = timedelta(minutes=settings.access_token_ttl_minutes)
    claims = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "sub": str(user_id),
        "sid": str(session_id),
        "iat": now,
        "exp": now + ttl,
        "jti": uuid.uuid4().hex,
        "token_use": "access",
    }
    token = jwt.encode(
        claims,
        settings.jwt_private_key.get_secret_value(),
        algorithm=ALGORITHM,
        headers={"kid": settings.jwt_key_id},
    )
    return token, int(ttl.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    claims: dict[str, Any] = jwt.decode(
        token,
        settings.jwt_public_key,
        algorithms=[ALGORITHM],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        leeway=10,
        options={"require": ["exp", "iat", "sub", "sid", "iss", "aud"]},
    )
    if claims.get("token_use") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return claims


def new_opaque_token() -> tuple[str, str]:
    """Value for the client, hash for the databse."""
    raw = secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest()


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
