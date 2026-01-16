"""
Configuration management for the Telegram Bot Store.
Loads settings from environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Pakasir Payment
    PAKASIR_PROJECT_SLUG: str = os.getenv("PAKASIR_PROJECT_SLUG", "")
    PAKASIR_API_KEY: str = os.getenv("PAKASIR_API_KEY", "")
    PAKASIR_API_BASE_URL: str = "https://app.pakasir.com/api"
    
    # Webhook
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "5000"))
    
    # Admin
    ADMIN_TELEGRAM_IDS: list[int] = [
        int(id.strip()) 
        for id in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",") 
        if id.strip()
    ]
    
    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./store.db")
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration. Returns list of missing configs."""
        errors = []
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        if not cls.PAKASIR_PROJECT_SLUG:
            errors.append("PAKASIR_PROJECT_SLUG is required")
        if not cls.PAKASIR_API_KEY:
            errors.append("PAKASIR_API_KEY is required")
        return errors


# Singleton instance
config = Config()
