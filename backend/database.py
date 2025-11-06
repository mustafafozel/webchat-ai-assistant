from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

# Veritabanı bağlantı motorunu oluştur
# 'check_same_thread' SQLite içindir, PostgreSQL için kaldıralım.
engine = create_engine(settings.DATABASE_URL)

# Veritabanı oturumu (session) oluşturucu
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modellerimizin miras alacağı temel sınıf
Base = declarative_base()

def get_db():
    """FastAPI Dependencies için veritabanı oturumu sağlar"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Uygulama başladığında veritabanı tablolarını oluşturur.
    (Bu, main.py içinden çağrılacak)
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("Veritabanı tabloları başarıyla oluşturuldu.")
    except Exception as e:
        print(f"Veritabanı tabloları oluşturulurken hata: {e}")
