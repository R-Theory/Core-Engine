from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/core_engine"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # External APIs
    CANVAS_CLIENT_ID: str = ""
    CANVAS_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # AI Agents
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    METAGPT_API_KEY: str = ""
    
    # File Storage
    UPLOAD_DIR: str = "/app/storage"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    class Config:
        env_file = ".env"

settings = Settings()