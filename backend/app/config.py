import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Lunar Aurora - Spatial Historical AI Guide"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # AI & Speech
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    DEFAULT_VOICE: str = "en-US-ChristopherNeural"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./lunar_aurora.db"
    )
    POSTGIS_URL: Optional[str] = os.getenv(
        "POSTGIS_URL",
        "postgresql://luna:aurora123@localhost:5432/lunar_aurora"
    )
    
    # Audio Storage
    AUDIO_CACHE_DIR: str = os.path.join(os.path.dirname(__file__), "..", "static", "audio")

    class Config:
        env_file = ".env"

settings = Settings()
os.makedirs(settings.AUDIO_CACHE_DIR, exist_ok=True)

