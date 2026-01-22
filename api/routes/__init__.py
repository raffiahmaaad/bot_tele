"""
Routes package.
"""

from .auth import auth_bp
from .bots import bots_bp
from .products import products_bp
from .transactions import transactions_bp
from .broadcast import broadcast_bp
from .sheerid import sheerid_bp
from .commands import commands_bp
from .categories import categories_bp

__all__ = [
    'auth_bp',
    'bots_bp', 
    'products_bp',
    'transactions_bp',
    'broadcast_bp',
    'sheerid_bp',
    'commands_bp',
    'categories_bp',
]

