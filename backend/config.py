import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://webchat_user:güçlü_şifre_123@localhost/webchat_db")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    CORS_ORIGINS = ["*"]
    
settings = Settings()
