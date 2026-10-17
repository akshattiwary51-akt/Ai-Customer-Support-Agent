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
    # ReAct agent. The agent engine is only used when a key is configured;
    # otherwise chat falls back to the deterministic router.
    agent_enabled: bool = True
    anthropic_api_key: str | None = None
    agent_model: str = "claude-sonnet-5-5"
    agent_max_steps: int = 6
    agent_max_tokens: int = 1024
    agent_timeout_seconds: float = 30.0
    agent_history_messages: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
