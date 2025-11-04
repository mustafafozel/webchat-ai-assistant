import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://webchat_user:webchat_password@db:5432/webchat_ai")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    CORS_ORIGINS = ["*"]

settings = Settings()
