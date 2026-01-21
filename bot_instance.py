"""
Bot Instance Module.
Wraps a single Telegram bot with its configuration and handlers.
"""

import logging
from telegram.ext import Application

logger = logging.getLogger(__name__)


class BotInstance:
    """Represents a single bot instance with its configuration."""
    
    def __init__(self, bot_config: dict):
        """
        Initialize bot instance.
        
        Args:
            bot_config: Dictionary with bot configuration from database
                - id: Bot ID
                - telegram_token: Telegram bot token
                - bot_username: Bot username
                - bot_name: Bot display name
                - bot_type: 'store', 'verification', or 'custom'
                - pakasir_slug: Pakasir project slug (for store bots)
                - pakasir_api_key: Pakasir API key (for store bots)
        """
        self.bot_id = bot_config['id']
        self.bot_type = bot_config.get('bot_type', 'store')
        self.bot_username = bot_config.get('bot_username', 'Unknown')
        self.bot_name = bot_config.get('bot_name', 'Unnamed Bot')
        self.pakasir_slug = bot_config.get('pakasir_slug')
        self.pakasir_api_key = bot_config.get('pakasir_api_key')
        
        # Build application
        self.app = Application.builder().token(bot_config['telegram_token']).build()
        
        # Store bot_id in bot_data for handlers to access
        self.app.bot_data['bot_id'] = self.bot_id
        self.app.bot_data['bot_type'] = self.bot_type
        self.app.bot_data['pakasir_slug'] = self.pakasir_slug
        self.app.bot_data['pakasir_api_key'] = self.pakasir_api_key
        
        # Register handlers based on type
        self._register_handlers()
    
    def _register_handlers(self):
        """Register handlers based on bot type."""
        if self.bot_type == 'store':
            self._register_store_handlers()
        elif self.bot_type == 'verification':
            self._register_verification_handlers()
        elif self.bot_type == 'points_verify':
            self._register_points_verify_handlers()
        elif self.bot_type == 'sheerid':
            self._register_sheerid_handlers()
        else:
            self._register_custom_handlers()
    
    def _register_store_handlers(self):
        """Register store bot handlers."""
        from handlers.store import get_all_store_handlers
        
        for handler in get_all_store_handlers(self.bot_id):
            self.app.add_handler(handler)
        
        logger.info(f"[{self.bot_username}] Store handlers registered")
    
    def _register_verification_handlers(self):
        """Register verification bot handlers."""
        from handlers.verification import get_all_verification_handlers
        
        for handler in get_all_verification_handlers(self.bot_id):
            self.app.add_handler(handler)
        
        logger.info(f"[{self.bot_username}] Verification handlers registered")
    
    def _register_points_verify_handlers(self):
        """Register points verification bot handlers (with PostgreSQL)."""
        from handlers.points_verify import get_all_points_verify_handlers
        
        # Points verify uses database_pg functions directly, no separate db instance needed
        for handler in get_all_points_verify_handlers(self.bot_id):
            self.app.add_handler(handler)
        
        logger.info(f"[{self.bot_username}] Points verification handlers registered")
    
    def _register_sheerid_handlers(self):
        """Register SheerID verification bot handlers."""
        from handlers.sheerid import get_sheerid_handlers
        
        # Register SheerID handlers (includes /start, /verify, and all callbacks)
        for handler in get_sheerid_handlers(self.bot_id):
            self.app.add_handler(handler)
        
        logger.info(f"[{self.bot_username}] SheerID verification handlers registered")
    
    def _register_custom_handlers(self):
        """Register minimal custom bot handlers."""
        from handlers.custom import get_custom_handlers
        
        for handler in get_custom_handlers(self.bot_id):
            self.app.add_handler(handler)
        
        logger.info(f"[{self.bot_username}] Custom handlers registered")
    
    async def start(self):
        """Initialize and start the bot (without blocking)."""
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        logger.info(f"✅ Bot started: @{self.bot_username} (ID: {self.bot_id}, Type: {self.bot_type})")
    
    async def stop(self):
        """Stop the bot."""
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        logger.info(f"⏹️ Bot stopped: @{self.bot_username}")
    
    def __repr__(self):
        return f"BotInstance(id={self.bot_id}, username={self.bot_username}, type={self.bot_type})"
