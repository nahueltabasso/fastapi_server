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

    jwt_private_key: SecretStr
    jwt_public_key: str
    jwt_key_id: str = "k1"
    jwt_issuer: str = "fastapi-base"
    jwt_audience: str = "fastapi-base-api"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7  # 7 day
    session_max_days: int = 30
    refresh_cookie_name: str = "refresh_token"

    email_verification_ttl_hours: int = 24
    password_reset_ttl_minutes: int = 5

    # Email settings
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_start_tls: bool = True
    mail_from: str
    frontend_url: str

    cors_origins: list[str] = []
    google_client_ids: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
