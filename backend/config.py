from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized application configuration."""

    APP_NAME: str = "WebChat AI Assistant"

    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    DATABASE_URL: Optional[str] = None
    SQLITE_URL: str = "sqlite+aiosqlite:///./webchat_ai.db"

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama3-70b-8192"

    KNOWLEDGE_BASE_PATH: Path = Path("knowledge/kb.json")

    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def database_url(self) -> str:
        """Return an async-compatible database URL with SQLite fallback."""
        if self.DATABASE_URL:
            return self.DATABASE_URL

        if self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_DB:
            return (
                "postgresql+asyncpg://"
                f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

        return self.SQLITE_URL

    @property
    def sync_database_url(self) -> str:
        """Return a synchronous driver version of the configured database URL."""
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        if url.startswith("sqlite+aiosqlite://"):
            return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return url


settings = Settings()
