"""
Multi-Bot Platform - Main Entry Point

A platform for running multiple Telegram bots of different types
(store, verification, custom) from a single server.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point - run the multi-bot platform."""
    from bot_manager import BotManager
    from database_pg import init_connection_pool, close_connection_pool
    
    # Check required env vars
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in .env")
        print("Please configure your PostgreSQL connection.")
        return
    
    owner_id = os.getenv("OWNER_TELEGRAM_ID")
    if not owner_id:
        print("⚠️ OWNER_TELEGRAM_ID not set - admin features will be disabled")
    
    # Initialize database connection pool for fast responses
    print("🔌 Initializing database connection pool...")
    try:
        init_connection_pool(minconn=2, maxconn=10)
        print("✅ Connection pool ready!")
    except Exception as e:
        print(f"❌ Failed to initialize connection pool: {e}")
        return
    
    # Run the bot manager
    manager = BotManager()
    
    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    finally:
        # Clean up connection pool
        close_connection_pool()


if __name__ == "__main__":
    main()
