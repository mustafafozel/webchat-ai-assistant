"""Database engines and session helpers."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import settings

# Async SQLAlchemy engine/session (FastAPI startup & background jobs)
async_engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def init_db() -> None:
    """Create database tables on startup."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_db():
    """FastAPI dependency that yields an async session."""
    async with AsyncSessionLocal() as session:
        yield session


# Sync engine/session pair for LangGraph workflow persistence
sync_engine = create_engine(settings.sync_database_url, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


def get_db():
    """Dependency that yields a synchronous session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
