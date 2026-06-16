"""Runtime configuration loaded from environment variables.

Settings are loaded once at import time and injected via FastAPI dependencies so
they can be overridden in tests. Anything that varies between local/staging/prod
belongs here, not buried in module-level constants.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["local", "test", "staging", "prod"] = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://hub:hub@localhost:5432/hub"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    meta_api_base_url: str = "https://graph.facebook.com/v20.0"
    meta_api_timeout_seconds: float = 15.0
    meta_use_mock: bool = True
    meta_mock_fail_rate: float = 0.0
    meta_mock_rate_limit_every: int = 0

    meta_oauth_client_id: str = "local-client-id"
    meta_oauth_client_secret: str = "local-client-secret"

    token_encryption_key: str = Field(
        default="changeme-changeme-changeme-changeme=",
        description="Symmetric key used to encrypt OAuth tokens at rest.",
    )

    meta_max_retries: int = 4
    meta_retry_base_delay_seconds: float = 0.5


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
