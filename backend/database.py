from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

# Asenkron SQLAlchemy motoru oluştur
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

# Asenkron session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ORM modelleri için Base sınıfı
Base = declarative_base()

# Veritabanı tablolarını oluşturmak için asenkron başlatıcı
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Session sağlayıcı (Dependency Injection)
async def get_db():
    async with async_session() as session:
        yield session

