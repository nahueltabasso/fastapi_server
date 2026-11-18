import asyncio
import unicodedata

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from fastapi_base.core.exceptions import BusinessLogicError, ErrorCode

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

_password_hash = PasswordHash(
    (Argon2Hasher(time_cost=2, memory_cost=19456, parallelism=1),)
)
_DUMMY_HASH = _password_hash.hash("dummy_password")


def _normalize(password: str) -> str:
    return unicodedata.normalize("NFKC", password)


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(_password_hash.hash, _normalize(password))


async def verify_password(
    password: str, password_hash: str | None
) -> tuple[bool, str | None]:
    valid, updated = await asyncio.to_thread(
        _password_hash.verify_and_update,
        _normalize(password),
        password_hash or _DUMMY_HASH,
    )
    return valid and password_hash is not None, updated


def check_password_policy(password: str, *, email: str) -> None:
    normalized = _normalize(password)
    lowered_pass = normalized.lower()
    local_part = email.split("@")[0].lower()
    if not MIN_PASSWORD_LENGTH <= len(normalized) <= MAX_PASSWORD_LENGTH:
        reason = f"Password must be between {MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH} characters long."
    elif len(local_part) >= 4 and local_part in lowered_pass:
        reason = "Password must not contain the local part of the email address."
    else:
        return
    raise BusinessLogicError(
        message=reason, error_code=ErrorCode.PASSWORD_POLICY_VIOLATION
    )
