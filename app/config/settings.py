from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables
    and the .env file.
    """

    # Application
    app_name: str = "LinkPlease"
    app_env: str = "development"

    # PseudoGram API
    pseudogram_base_url: str = "https://pseudogram-api.onrender.com"
    pseudogram_api_key: str = Field(default="your_api_key_here")

    # Database
    database_url: str = "sqlite:///./linkplease.db"

    # Retry configuration
    max_retries: int = Field(default=3, ge=0)
    initial_retry_delay: float = Field(default=2.0, gt=0)

    # PseudoGram rate limit
    rate_limit_requests: int = Field(default=10, gt=0)
    rate_limit_window_seconds: int = Field(default=60, gt=0)

    # Delivery reconciliation
    delivery_check_interval_seconds: int = Field(default=5, gt=0)
    delivery_max_attempts: int = Field(default=5, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Caching ensures that the application uses one consistent
    configuration object throughout its lifetime.
    """
    return Settings()