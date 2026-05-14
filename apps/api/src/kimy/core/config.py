from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "KIMY API"
    app_version: str = "0.1.0"
    environment: str = Field(default="development")
    debug: bool = True

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    database_url: str = "postgresql+asyncpg://kimy:kimy@localhost:5433/kimy"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-prod"
    encryption_key: str = "change-me-in-prod-32-bytes-base64-fernet="

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    orcid_client_id: str | None = None
    orcid_client_secret: str | None = None
    orcid_redirect_uri: str = "http://localhost:3000/orcid/callback"

    crossref_user_agent: str = "KIMY/0.1 (mailto:contact@example.com)"

    storage_backend: str = "local"
    storage_path: str = "./storage"


@lru_cache
def get_settings() -> Settings:
    return Settings()
