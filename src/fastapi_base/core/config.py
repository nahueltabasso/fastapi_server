from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="APP_", extra="ignore"
    )

    env: Literal["local", "test", "production"] = "local"
    project_name: str = "fastapi-base"
    api_prefix: str = "/api/v1"
    json_logs: bool = False
    logging_level: str = "INFO"

    database_url: PostgresDsn
    db_pool_size: int = 10
    db_max_overflow: int = 5
    db_pool_timeout: int = 30

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_minutes: int = 60 * 24 * 7  # 7 days

    cors_origins: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
