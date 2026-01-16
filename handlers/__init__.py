"""Handlers package."""
from handlers.start import get_start_handlers
from handlers.catalog import get_catalog_handlers
from handlers.order import get_order_handlers
from handlers.admin import get_admin_handlers

__all__ = [
    "get_start_handlers",
    "get_catalog_handlers",
    "get_order_handlers",
    "get_admin_handlers"
]
