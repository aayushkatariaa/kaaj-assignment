from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    DB_USER: str = "loan_user"
    DB_PASSWORD: str = "loan_pass"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "loan_underwriting"

    # Server
    PORT: int = 8000
    DEBUG: bool = True
    
    # JWT
    JWT_ALGO: str = "HS256"
    JWT_SECRET: str = "your-secret-key-change-in-production"
    
    # Hatchet
    HATCHET_CLIENT_TOKEN: Optional[str] = None
    
    # AI Provider for PDF parsing
    AI_PROVIDER: str = "openai"  # Options: "openai" or "gemini"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
