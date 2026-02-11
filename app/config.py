"""Application configuration via Pydantic Settings v2."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+psycopg://jobhunter:jobhunter123@localhost:5433/jobhunter_db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # APIs — Tier 2 (optional, key required)
    jooble_api_key: str = ""
    adzuna_app_id: str = ""
    adzuna_api_key: str = ""
    serpapi_key: str = ""

    # AI
    anthropic_api_key: str = ""

    # User settings
    min_salary_usd: int = 50000
    max_salary_usd: int = 80000
    target_roles: str = "backend,fullstack,rails,ruby,go,golang,react,python,smalltalk,postgresql"
    target_seniority: str = "mid,senior,lead"

    # Notifications
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_email: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # App
    env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    @property
    def target_roles_list(self) -> list[str]:
        """Parse comma-separated target roles into a list."""
        return [r.strip() for r in self.target_roles.split(",") if r.strip()]

    @property
    def target_seniority_list(self) -> list[str]:
        """Parse comma-separated seniority levels into a list."""
        return [s.strip() for s in self.target_seniority.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
