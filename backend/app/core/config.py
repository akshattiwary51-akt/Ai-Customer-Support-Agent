from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ResolveAI Support API"
    environment: str = "local"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./support_agent.db"
    jwt_secret: str = Field(default="dev-only-change-me", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8
    allowed_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    auto_create_tables: bool = True
    max_upload_bytes: int = 5_000_000
    retrieval_top_k: int = 4
    retrieval_min_score: float = 0.08
    refund_window_days: int = 30
    rate_limit_per_minute: int = 120

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
