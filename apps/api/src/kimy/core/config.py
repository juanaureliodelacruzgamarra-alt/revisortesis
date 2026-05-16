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

    app_name: str = "Aurelio API"
    app_version: str = "0.1.0"
    environment: str = Field(default="development")
    debug: bool = True

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    database_url: str = "postgresql+asyncpg://kimy:kimy@localhost:5433/kimy"
    redis_url: str = "redis://localhost:6379/0"

    # Minimum 32 bytes for HS256 (RFC 7518 §3.2). Override in production.
    jwt_secret: str = "dev-only-secret-change-me-32bytes-min-padding-padding"  # noqa: S105
    encryption_key: str = "change-me-in-prod-32-bytes-base64-fernet="  # noqa: S105

    # Primary LLM provider: Google Gemini (via google-genai SDK).
    gemini_api_key: str | None = None
    # Legacy / fallback LLM providers — optional.
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    orcid_client_id: str | None = None
    orcid_client_secret: str | None = None
    orcid_redirect_uri: str = "http://localhost:3000/orcid/callback"
    # Use ORCID sandbox by default (sandbox.orcid.org). Set to false for prod.
    orcid_sandbox: bool = True

    # Cosine similarity below this is flagged as a poor advisor↔thesis match.
    # 0.35 is calibrated for the hashed-BoW embedder; raise to ~0.50 when running
    # with OpenAI text-embedding-3-small (which discriminates more sharply).
    orcid_advisor_fit_threshold: float = 0.35

    crossref_user_agent: str = "Aurelio/0.1 (mailto:contact@example.com)"

    storage_backend: str = "local"
    storage_path: str = "./storage"


@lru_cache
def get_settings() -> Settings:
    return Settings()
