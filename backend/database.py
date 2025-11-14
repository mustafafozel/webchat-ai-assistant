from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker as sync_sessionmaker
from backend.config import settings

<<<<<<< HEAD
# Asenkron SQLAlchemy motoru oluştur
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

# Asenkron session factory
=======
# === ASYNC (Asenkron) Bölüm ===
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ORM modelleri için Base sınıfı
Base = declarative_base()

<<<<<<< HEAD
# Veritabanı tablolarını oluşturmak için asenkron başlatıcı
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Session sağlayıcı (Dependency Injection)
async def get_db():
    async with async_session() as session:
        yield session
=======
async def init_db():
    """Veritabanı tablolarını oluştur (async)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_db():
    """Async session sağlayıcı"""
    async with async_session() as session:
        yield session

# === SYNC (Senkron) Bölüm ===
# LangGraph gibi sync kodlar için

def get_sync_database_url() -> str:
    """
    Async URL'yi sync URL'ye çevir
    postgresql+asyncpg:// → postgresql://
    """
    url = settings.DATABASE_URL
    if "postgresql+asyncpg://" in url:
        return url.replace("postgresql+asyncpg://", "postgresql://")
    return url

# Senkron engine
sync_engine = create_engine(
    get_sync_database_url(),
    echo=False,
    pool_pre_ping=True  # Bağlantı kontrolü
)

# Senkron session factory
SessionLocal = sync_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

def get_db():
    """Senkron session sağlayıcı (LangGraph run_agent için)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
>>>>>>> 65eb5aa (feat: major update - LangGraph ReAct agent implementation)

