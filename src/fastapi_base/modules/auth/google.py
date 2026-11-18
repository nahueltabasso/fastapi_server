import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol

import jwt

from fastapi_base.core.config import get_settings

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = frozenset(
    [
        "https://accounts.google.com",
        "accounts.google.com",
    ]
)


@dataclass(frozen=True, slots=True)
class GoogleIdentity:
    subject: str
    email: str
    email_verified: bool
    hosted_domain: str | None
    name: str | None

    @property
    def is_authorative(self) -> bool:
        """Google is the owner of the email. Gmail accounts or Google Workspace."""
        return self.email_verified and (
            self.email.endswith("@gmail.com") or (self.hosted_domain is not None)
        )


class GoogleVerifier(Protocol):
    async def verify(self, id_token: str) -> GoogleIdentity: ...


class GoogleTokenVerifier:
    def __init__(self, client_ids: list[str]) -> None:
        self._jwks = jwt.PyJWKClient(GOOGLE_JWKS_URL, cache_keys=True)
        self._client_ids = client_ids

    async def verify(self, id_token: str) -> GoogleIdentity:
        key = await asyncio.to_thread(self._jwks.get_signing_key_from_jwt, id_token)
        claims: dict[str, Any] = jwt.decode(
            id_token,
            key.key,
            algorithms=["RS256"],
            audience=self._client_ids,
            leeway=10,
            options={"require": ["exp", "iat", "sub", "iss", "aud", "email"]},
        )

        if claims["iss"] not in GOOGLE_ISSUERS:
            raise jwt.InvalidIssuerError("Not issued by Google")
        return GoogleIdentity(
            subject=claims["sub"],
            email=claims["email"].strip(),
            email_verified=claims["email_verified"],
            hosted_domain=claims.get("hd"),
            name=claims.get("name"),
        )


@lru_cache
def get_google_verifier() -> GoogleVerifier:
    return GoogleTokenVerifier(get_settings().google_client_ids)
