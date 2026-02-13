from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # API Keys
    anthropic_api_key: str = ""
    ncbi_api_key: str = ""  # Optional: for higher rate limits
    analytics_api_key: str = ""  # Optional: protects /api/analytics endpoints

    # App settings
    app_name: str = "PubMed Translator & Summarizer"
    debug: bool = False

    # CORS settings
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Claude settings
    claude_model: str = "claude-sonnet-4-20250514"

    # Database settings
    database_url: str = "postgresql://localhost:5432/brobiotic"

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),  # Check parent dir first, then current
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
