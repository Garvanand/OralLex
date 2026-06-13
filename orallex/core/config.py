"""
OralLex Configuration.
"""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    
    postgres_url: str = os.getenv("POSTGRES_URL", "postgresql+asyncpg://agentos:agentos_password@localhost:5432/agentos_shared")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8000"))

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    environment: str = os.getenv("ENVIRONMENT", "development")

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
