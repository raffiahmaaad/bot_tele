"""
Digital Store Telegram Bot - Main Entry Point

A Telegram bot for digital product store with QRIS payment integration via Pakasir.
"""

import asyncio
import logging
import sys

from telegram import Update
from telegram.ext import Application

from config import config
from database import init_database
from handlers import (
    get_start_handlers,
    get_catalog_handlers,
    get_order_handlers,
    get_admin_handlers
)
from webhook import run_webhook_server, set_bot_reference


# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the bot."""
    print("=" * 50)
    print("🤖 Digital Store Telegram Bot")
    print("=" * 50)
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("\n❌ Configuration errors:")
        for error in errors:
            print(f"   • {error}")
        print("\n📝 Please copy .env.example to .env and fill in your credentials.")
        sys.exit(1)
    
    print("\n✅ Configuration loaded")
    print(f"   • Pakasir Project: {config.PAKASIR_PROJECT_SLUG}")
    print(f"   • Webhook Port: {config.WEBHOOK_PORT}")
    print(f"   • Admin IDs: {config.ADMIN_TELEGRAM_IDS}")
    
    # Initialize database
    print("\n📦 Initializing database...")
    init_database()
    
    # Create application
    print("\n🔧 Creating bot application...")
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers
    # Admin handlers first (includes conversation handlers)
    for handler in get_admin_handlers():
        application.add_handler(handler)
    
    # Then other handlers
    for handler in get_start_handlers():
        application.add_handler(handler)
    
    for handler in get_catalog_handlers():
        application.add_handler(handler)
    
    for handler in get_order_handlers():
        application.add_handler(handler)
    
    print("✅ All handlers registered")
    
    # Start webhook server in background thread
    print(f"\n🌐 Starting webhook server on port {config.WEBHOOK_PORT}...")
    
    # Get the event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Set bot reference for webhook to use
    set_bot_reference(application.bot, loop)
    
    # Start webhook server
    run_webhook_server(config.WEBHOOK_PORT)
    
    # Start the bot
    print("\n🚀 Starting bot...")
    print("=" * 50)
    print("Bot is running! Press Ctrl+C to stop.")
    print("=" * 50)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
