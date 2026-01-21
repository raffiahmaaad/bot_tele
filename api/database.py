"""
Database connection and models for multi-tenant SaaS platform.
Uses Neon PostgreSQL.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime
from typing import Optional
from config import config


@contextmanager
def get_connection():
    """Get database connection with context manager."""
    conn = psycopg2.connect(config.DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor():
    """Get database cursor with context manager."""
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
        finally:
            cursor.close()


def init_database():
    """Initialize database schema."""
    with get_cursor() as cursor:
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Bots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                telegram_token VARCHAR(255) NOT NULL,
                bot_username VARCHAR(100),
                bot_name VARCHAR(100),
                bot_type VARCHAR(50) DEFAULT 'store',
                pakasir_slug VARCHAR(100),
                pakasir_api_key VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT true,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                content_type VARCHAR(50) DEFAULT 'text',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Product Stock (credentials/vouchers)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_stock (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                is_sold BOOLEAN DEFAULT false,
                sold_at TIMESTAMP,
                order_id INTEGER
            )
        """)
        
        # Bot Users (Telegram users who use the bots)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_users (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                telegram_id BIGINT NOT NULL,
                username VARCHAR(100),
                first_name VARCHAR(100),
                is_blocked BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(bot_id, telegram_id)
            )
        """)
        
        # Orders/Transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                bot_user_id INTEGER REFERENCES bot_users(id),
                product_id INTEGER REFERENCES products(id),
                order_id VARCHAR(50) UNIQUE NOT NULL,
                amount INTEGER NOT NULL,
                fee INTEGER DEFAULT 0,
                total INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                payment_method VARCHAR(50),
                qris_string TEXT,
                expired_at TIMESTAMP,
                paid_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Broadcasts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS broadcasts (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                message TEXT NOT NULL,
                recipients_count INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP
            )
        """)
        
        print("✅ Database initialized successfully")


# ==================== USER OPERATIONS ====================

def create_user(email: str, password_hash: str, name: str = None) -> Optional[dict]:
    """Create a new user."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO users (email, password_hash, name)
            VALUES (%s, %s, %s)
            RETURNING id, email, name, created_at
        """, (email, password_hash, name))
        return dict(cursor.fetchone())


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, email, password_hash, name, created_at
            FROM users WHERE email = %s
        """, (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get user by ID."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, email, name, created_at
            FROM users WHERE id = %s
        """, (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# ==================== BOT OPERATIONS ====================

def create_bot(user_id: int, telegram_token: str, bot_username: str = None, bot_name: str = None, 
               bot_type: str = 'store', pakasir_slug: str = None, pakasir_api_key: str = None) -> Optional[dict]:
    """Create a new bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO bots (user_id, telegram_token, bot_username, bot_name, bot_type, pakasir_slug, pakasir_api_key)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, telegram_token, bot_username, bot_name, bot_type, is_active, created_at
        """, (user_id, telegram_token, bot_username, bot_name, bot_type, pakasir_slug, pakasir_api_key))
        return dict(cursor.fetchone())


def get_bots_by_user(user_id: int) -> list[dict]:
    """Get all bots for a user."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT b.*, 
                   (SELECT COUNT(*) FROM products WHERE bot_id = b.id) as products_count,
                   (SELECT COUNT(*) FROM bot_users WHERE bot_id = b.id) as users_count,
                   (SELECT COUNT(*) FROM orders WHERE bot_id = b.id AND status = 'completed') as transactions_count
            FROM bots b
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_bot_by_id(bot_id: int, user_id: int = None) -> Optional[dict]:
    """Get bot by ID, optionally filtering by user."""
    with get_cursor() as cursor:
        query = "SELECT * FROM bots WHERE id = %s"
        params = [bot_id]
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def update_bot(bot_id: int, **kwargs) -> Optional[dict]:
    """Update a bot."""
    allowed_fields = ['bot_name', 'bot_type', 'pakasir_slug', 'pakasir_api_key', 'is_active']
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
    
    if not updates:
        return get_bot_by_id(bot_id)
    
    with get_cursor() as cursor:
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        set_clause += ", updated_at = NOW()"
        values = list(updates.values()) + [bot_id]
        
        cursor.execute(f"""
            UPDATE bots SET {set_clause}
            WHERE id = %s
            RETURNING *
        """, values)
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_bot(bot_id: int) -> bool:
    """Delete a bot."""
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM bots WHERE id = %s", (bot_id,))
        return cursor.rowcount > 0


# ==================== PRODUCT OPERATIONS ====================

def create_product(bot_id: int, name: str, price: int, category_id: int = None, description: str = None) -> Optional[dict]:
    """Create a new product."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO products (bot_id, category_id, name, price, description)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (bot_id, category_id, name, price, description))
        return dict(cursor.fetchone())


def get_products_by_bot(bot_id: int) -> list[dict]:
    """Get all products for a bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT p.*, 
                   c.name as category_name,
                   (SELECT COUNT(*) FROM product_stock WHERE product_id = p.id AND is_sold = false) as stock,
                   (SELECT COUNT(*) FROM product_stock WHERE product_id = p.id AND is_sold = true) as sold
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.bot_id = %s
            ORDER BY p.created_at DESC
        """, (bot_id,))
        return [dict(row) for row in cursor.fetchall()]


def add_product_stock(product_id: int, contents: list[str]) -> int:
    """Add stock items to a product. Returns count of items added."""
    with get_cursor() as cursor:
        for content in contents:
            cursor.execute("""
                INSERT INTO product_stock (product_id, content)
                VALUES (%s, %s)
            """, (product_id, content.strip()))
        return len(contents)


# ==================== TRANSACTION OPERATIONS ====================

def get_transactions_by_bot(bot_id: int, limit: int = 50) -> list[dict]:
    """Get transactions for a bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT o.*, 
                   p.name as product_name,
                   bu.username as buyer_username,
                   bu.first_name as buyer_name
            FROM orders o
            LEFT JOIN products p ON o.product_id = p.id
            LEFT JOIN bot_users bu ON o.bot_user_id = bu.id
            WHERE o.bot_id = %s
            ORDER BY o.created_at DESC
            LIMIT %s
        """, (bot_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def get_bot_stats(bot_id: int) -> dict:
    """Get statistics for a bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM products WHERE bot_id = %s) as total_products,
                (SELECT COUNT(*) FROM bot_users WHERE bot_id = %s) as total_users,
                (SELECT COUNT(*) FROM orders WHERE bot_id = %s AND status = 'completed') as total_transactions,
                (SELECT COALESCE(SUM(amount), 0) FROM orders WHERE bot_id = %s AND status = 'completed') as total_revenue
        """, (bot_id, bot_id, bot_id, bot_id))
        return dict(cursor.fetchone())


# ==================== BROADCAST OPERATIONS ====================

def create_broadcast(bot_id: int, message: str) -> Optional[dict]:
    """Create a broadcast record."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO broadcasts (bot_id, message)
            VALUES (%s, %s)
            RETURNING *
        """, (bot_id, message))
        return dict(cursor.fetchone())


def get_broadcasts_by_bot(bot_id: int, limit: int = 20) -> list[dict]:
    """Get broadcasts for a bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM broadcasts
            WHERE bot_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (bot_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def get_bot_users_for_broadcast(bot_id: int) -> list[dict]:
    """Get all non-blocked users for broadcast."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT telegram_id, username, first_name
            FROM bot_users
            WHERE bot_id = %s AND is_blocked = false
        """, (bot_id,))
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    init_database()
