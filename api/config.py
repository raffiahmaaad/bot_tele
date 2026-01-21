"""
Configuration for API Backend.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES: int = 60 * 60 * 24  # 24 hours
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://botstore.vercel.app",
        "https://bot-teleraf.vercel.app",
    ]
    
    # API
    API_PREFIX: str = "/api"
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration."""
        errors = []
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        return errors


config = Config()
