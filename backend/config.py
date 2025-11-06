import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

class Settings:
    # Veritabanı
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # AI Ayarları
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "distiluse-base-multilingual-cased-v1")
    
    # RAG Ayarları
    RAG_INDEX_PATH = os.getenv("RAG_INDEX_PATH", "./faiss_index")
    KNOWLEDGE_BASE_FILE = os.getenv("KNOWLEDGE_BASE_FILE", "knowledge/kb.json")

settings = Settings()
