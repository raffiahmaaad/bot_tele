"""
Database connection for Bot Runner.
Connects to the same PostgreSQL database as the API.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Owner Telegram ID - has unlimited points
OWNER_TELEGRAM_ID = int(os.getenv("OWNER_TELEGRAM_ID", "0"))


@contextmanager
def get_connection():
    """Get database connection with context manager."""
    conn = psycopg2.connect(DATABASE_URL)
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


# ==================== BOT OPERATIONS ====================

def get_active_bots() -> list[dict]:
    """Get all active bots from database."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, user_id, telegram_token, bot_username, bot_name,
                   pakasir_slug, pakasir_api_key, bot_type, is_active
            FROM bots
            WHERE is_active = true
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_bot_by_id(bot_id: int) -> Optional[dict]:
    """Get bot by ID."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, user_id, telegram_token, bot_username, bot_name,
                   pakasir_slug, pakasir_api_key, bot_type, is_active
            FROM bots WHERE id = %s
        """, (bot_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_bot_owner_telegram_id(bot_id: int) -> Optional[int]:
    """Get the Telegram ID of the bot owner (for admin check)."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT u.telegram_id
            FROM bots b
            JOIN users u ON b.user_id = u.id
            WHERE b.id = %s
        """, (bot_id,))
        row = cursor.fetchone()
        return row['telegram_id'] if row else None


# ==================== BOT USER OPERATIONS ====================

def get_or_create_bot_user(bot_id: int, telegram_id: int, username: str = None, first_name: str = None) -> dict:
    """Get or create a bot user."""
    with get_cursor() as cursor:
        # Try to get existing
        cursor.execute("""
            SELECT * FROM bot_users
            WHERE bot_id = %s AND telegram_id = %s
        """, (bot_id, telegram_id))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        
        # Create new
        cursor.execute("""
            INSERT INTO bot_users (bot_id, telegram_id, username, first_name)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        """, (bot_id, telegram_id, username, first_name))
        return dict(cursor.fetchone())


def get_bot_user(bot_id: int, telegram_id: int) -> Optional[dict]:
    """Get bot user by telegram ID."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM bot_users
            WHERE bot_id = %s AND telegram_id = %s
        """, (bot_id, telegram_id))
        row = cursor.fetchone()
        return dict(row) if row else None


# ==================== CATEGORY OPERATIONS ====================

def get_categories_by_bot(bot_id: int, active_only: bool = True) -> list[dict]:
    """Get categories for a bot."""
    with get_cursor() as cursor:
        query = "SELECT * FROM categories WHERE bot_id = %s"
        if active_only:
            query += " AND is_active = true"
        query += " ORDER BY sort_order, name"
        cursor.execute(query, (bot_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_category_by_id(category_id: int) -> Optional[dict]:
    """Get category by ID."""
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_category(bot_id: int, name: str, description: str = None) -> dict:
    """Create a new category."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO categories (bot_id, name, description)
            VALUES (%s, %s, %s)
            RETURNING *
        """, (bot_id, name, description))
        return dict(cursor.fetchone())


def update_category(category_id: int, **kwargs) -> Optional[dict]:
    """Update a category."""
    allowed = ['name', 'description', 'is_active', 'sort_order']
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    
    if not updates:
        return get_category_by_id(category_id)
    
    with get_cursor() as cursor:
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [category_id]
        cursor.execute(f"""
            UPDATE categories SET {set_clause}
            WHERE id = %s RETURNING *
        """, values)
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_category(category_id: int) -> bool:
    """Delete a category."""
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        return cursor.rowcount > 0


# ==================== PRODUCT OPERATIONS ====================

def get_products_by_bot(bot_id: int, active_only: bool = True) -> list[dict]:
    """Get all products for a bot."""
    with get_cursor() as cursor:
        query = """
            SELECT p.*, c.name as category_name,
                   (SELECT COUNT(*) FROM product_stock WHERE product_id = p.id AND is_sold = false) as stock
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.bot_id = %s
        """
        if active_only:
            query += " AND p.is_active = true"
        query += " ORDER BY p.name"
        cursor.execute(query, (bot_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_products_by_category(category_id: int, bot_id: int, active_only: bool = True) -> list[dict]:
    """Get products in a category."""
    with get_cursor() as cursor:
        query = """
            SELECT p.*,
                   (SELECT COUNT(*) FROM product_stock WHERE product_id = p.id AND is_sold = false) as stock
            FROM products p
            WHERE p.category_id = %s AND p.bot_id = %s
        """
        if active_only:
            query += " AND p.is_active = true"
        query += " ORDER BY p.name"
        cursor.execute(query, (category_id, bot_id))
        return [dict(row) for row in cursor.fetchall()]


def get_product_by_id(product_id: int) -> Optional[dict]:
    """Get product by ID."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT p.*,
                   (SELECT COUNT(*) FROM product_stock WHERE product_id = p.id AND is_sold = false) as stock
            FROM products p
            WHERE p.id = %s
        """, (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_product(bot_id: int, category_id: int, name: str, price: int, description: str = None) -> dict:
    """Create a new product."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO products (bot_id, category_id, name, price, description)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (bot_id, category_id, name, price, description))
        return dict(cursor.fetchone())


def update_product(product_id: int, **kwargs) -> Optional[dict]:
    """Update a product."""
    allowed = ['name', 'description', 'price', 'category_id', 'is_active']
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    
    if not updates:
        return get_product_by_id(product_id)
    
    with get_cursor() as cursor:
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        set_clause += ", updated_at = NOW()"
        values = list(updates.values()) + [product_id]
        cursor.execute(f"""
            UPDATE products SET {set_clause}
            WHERE id = %s RETURNING *
        """, values)
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_product(product_id: int) -> bool:
    """Delete a product."""
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        return cursor.rowcount > 0


# ==================== STOCK OPERATIONS ====================

def get_available_stock(product_id: int) -> Optional[dict]:
    """Get one available stock item (not sold)."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM product_stock
            WHERE product_id = %s AND is_sold = false
            LIMIT 1
        """, (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def mark_stock_sold(stock_id: int, order_id: int) -> bool:
    """Mark a stock item as sold."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE product_stock
            SET is_sold = true, sold_at = NOW(), order_id = %s
            WHERE id = %s
        """, (order_id, stock_id))
        return cursor.rowcount > 0


def add_stock_items(product_id: int, contents: list[str]) -> int:
    """Add multiple stock items to a product."""
    with get_cursor() as cursor:
        for content in contents:
            cursor.execute("""
                INSERT INTO product_stock (product_id, content)
                VALUES (%s, %s)
            """, (product_id, content.strip()))
        return len(contents)


# ==================== ORDER OPERATIONS ====================

def create_order(
    bot_id: int,
    bot_user_id: int,
    product_id: int,
    order_id: str,
    amount: int,
    fee: int = 0,
    total: int = 0,
    qris_string: str = None,
    expired_at: datetime = None
) -> dict:
    """Create a new order."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO orders (bot_id, bot_user_id, product_id, order_id, amount, fee, total, qris_string, expired_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (bot_id, bot_user_id, product_id, order_id, amount, fee, total, qris_string, expired_at))
        return dict(cursor.fetchone())


def get_order_by_order_id(order_id: str) -> Optional[dict]:
    """Get order by Pakasir order ID."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT o.*, p.name as product_name, bu.telegram_id
            FROM orders o
            LEFT JOIN products p ON o.product_id = p.id
            LEFT JOIN bot_users bu ON o.bot_user_id = bu.id
            WHERE o.order_id = %s
        """, (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_orders_by_bot(bot_id: int, limit: int = 50) -> list[dict]:
    """Get orders for a bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT o.*, p.name as product_name, bu.username, bu.first_name
            FROM orders o
            LEFT JOIN products p ON o.product_id = p.id
            LEFT JOIN bot_users bu ON o.bot_user_id = bu.id
            WHERE o.bot_id = %s
            ORDER BY o.created_at DESC
            LIMIT %s
        """, (bot_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def get_orders_by_user(bot_id: int, bot_user_id: int, limit: int = 10) -> list[dict]:
    """Get orders for a specific user."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT o.*, p.name as product_name
            FROM orders o
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.bot_id = %s AND o.bot_user_id = %s
            ORDER BY o.created_at DESC
            LIMIT %s
        """, (bot_id, bot_user_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def update_order_status(order_id: str, status: str, paid_at: datetime = None) -> bool:
    """Update order status."""
    with get_cursor() as cursor:
        if paid_at:
            cursor.execute("""
                UPDATE orders SET status = %s, paid_at = %s
                WHERE order_id = %s
            """, (status, paid_at, order_id))
        else:
            cursor.execute("""
                UPDATE orders SET status = %s
                WHERE order_id = %s
            """, (status, order_id))
        return cursor.rowcount > 0


def get_bot_stats(bot_id: int) -> dict:
    """Get statistics for a bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM products WHERE bot_id = %s) as total_products,
                (SELECT COUNT(*) FROM bot_users WHERE bot_id = %s) as total_users,
                (SELECT COUNT(*) FROM orders WHERE bot_id = %s AND status = 'paid') as total_orders,
                (SELECT COALESCE(SUM(amount), 0) FROM orders WHERE bot_id = %s AND status = 'paid') as total_revenue
        """, (bot_id, bot_id, bot_id, bot_id))
        return dict(cursor.fetchone())


# ==================== VERIFICATION OPERATIONS ====================

def create_verification(bot_id: int, telegram_id: int, student_id: str, full_name: str) -> dict:
    """Create a new verification request."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO verifications (bot_id, telegram_id, student_id, full_name, status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING *
        """, (bot_id, telegram_id, student_id, full_name))
        return dict(cursor.fetchone())


def get_verification_by_telegram(bot_id: int, telegram_id: int) -> Optional[dict]:
    """Get verification by telegram ID."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM verifications
            WHERE bot_id = %s AND telegram_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (bot_id, telegram_id))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_pending_verifications(bot_id: int) -> list[dict]:
    """Get all pending verifications for a bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM verifications
            WHERE bot_id = %s AND status = 'pending'
            ORDER BY created_at ASC
        """, (bot_id,))
        return [dict(row) for row in cursor.fetchall()]


def update_verification_status(verification_id: int, status: str) -> bool:
    """Update verification status (approved/rejected)."""
    with get_cursor() as cursor:
        if status == 'approved':
            cursor.execute("""
                UPDATE verifications SET status = %s, verified_at = NOW()
                WHERE id = %s
            """, (status, verification_id))
        else:
            cursor.execute("""
                UPDATE verifications SET status = %s
                WHERE id = %s
            """, (status, verification_id))
        return cursor.rowcount > 0


# ==================== POINTS VERIFY OPERATIONS ====================

def get_or_create_pv_user(bot_id: int, telegram_id: int, username: str = None, full_name: str = None, invited_by: int = None) -> dict:
    """Get or create a points verify user with balance."""
    with get_cursor() as cursor:
        # Try to get existing
        cursor.execute("""
            SELECT * FROM pv_users
            WHERE bot_id = %s AND telegram_id = %s
        """, (bot_id, telegram_id))
        row = cursor.fetchone()
        
        if row:
            user_dict = dict(row)
            # Owner gets unlimited balance display
            if telegram_id == OWNER_TELEGRAM_ID:
                user_dict['balance'] = 999999
            return user_dict
        
        # Create new with initial balance
        cursor.execute("""
            INSERT INTO pv_users (bot_id, telegram_id, username, full_name, balance, invited_by)
            VALUES (%s, %s, %s, %s, 1, %s)
            RETURNING *
        """, (bot_id, telegram_id, username, full_name, invited_by))
        new_user = dict(cursor.fetchone())
        
        # If invited, give reward to inviter
        if invited_by:
            cursor.execute("""
                UPDATE pv_users SET balance = balance + 2
                WHERE bot_id = %s AND telegram_id = %s
            """, (bot_id, invited_by))
            
            # Record invitation
            cursor.execute("""
                INSERT INTO pv_invitations (bot_id, inviter_id, invitee_id)
                VALUES (%s, %s, %s)
            """, (bot_id, invited_by, telegram_id))
        
        # Owner gets unlimited balance display
        if telegram_id == OWNER_TELEGRAM_ID:
            new_user['balance'] = 999999
        
        return new_user


def get_pv_user(bot_id: int, telegram_id: int) -> Optional[dict]:
    """Get points verify user."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM pv_users
            WHERE bot_id = %s AND telegram_id = %s
        """, (bot_id, telegram_id))
        row = cursor.fetchone()
        if row:
            user_dict = dict(row)
            # Owner gets unlimited balance display
            if telegram_id == OWNER_TELEGRAM_ID:
                user_dict['balance'] = 999999
            return user_dict
        return None


def pv_user_exists(bot_id: int, telegram_id: int) -> bool:
    """Check if user exists."""
    return get_pv_user(bot_id, telegram_id) is not None


def is_pv_user_blocked(bot_id: int, telegram_id: int) -> bool:
    """Check if user is blocked."""
    user = get_pv_user(bot_id, telegram_id)
    return user and user.get('is_blocked', False)


def block_pv_user(bot_id: int, telegram_id: int) -> bool:
    """Block a user."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE pv_users SET is_blocked = true
            WHERE bot_id = %s AND telegram_id = %s
        """, (bot_id, telegram_id))
        return cursor.rowcount > 0


def unblock_pv_user(bot_id: int, telegram_id: int) -> bool:
    """Unblock a user."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE pv_users SET is_blocked = false
            WHERE bot_id = %s AND telegram_id = %s
        """, (bot_id, telegram_id))
        return cursor.rowcount > 0


def get_pv_blacklist(bot_id: int) -> list[dict]:
    """Get blocked users list."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM pv_users
            WHERE bot_id = %s AND is_blocked = true
        """, (bot_id,))
        return [dict(row) for row in cursor.fetchall()]


def add_pv_balance(bot_id: int, telegram_id: int, amount: int) -> bool:
    """Add balance to user."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE pv_users SET balance = balance + %s
            WHERE bot_id = %s AND telegram_id = %s
        """, (amount, bot_id, telegram_id))
        return cursor.rowcount > 0


def deduct_pv_balance(bot_id: int, telegram_id: int, amount: int) -> bool:
    """Deduct balance from user (checks if sufficient).
    Owner (OWNER_TELEGRAM_ID) is never deducted - unlimited points.
    """
    # Owner has unlimited points - never deduct
    if telegram_id == OWNER_TELEGRAM_ID:
        return True
    
    user = get_pv_user(bot_id, telegram_id)
    if not user or user.get('balance', 0) < amount:
        return False
    
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE pv_users SET balance = balance - %s
            WHERE bot_id = %s AND telegram_id = %s AND balance >= %s
        """, (amount, bot_id, telegram_id, amount))
        return cursor.rowcount > 0


def can_pv_checkin(bot_id: int, telegram_id: int) -> bool:
    """Check if user can check-in today."""
    user = get_pv_user(bot_id, telegram_id)
    if not user:
        return False
    
    last_checkin = user.get('last_checkin')
    if not last_checkin:
        return True
    
    from datetime import date
    return last_checkin.date() < date.today()


def pv_checkin(bot_id: int, telegram_id: int) -> bool:
    """Perform daily check-in."""
    with get_cursor() as cursor:
        cursor.execute("""
            UPDATE pv_users
            SET balance = balance + 1, last_checkin = NOW()
            WHERE bot_id = %s AND telegram_id = %s
            AND (last_checkin IS NULL OR DATE(last_checkin) < CURRENT_DATE)
        """, (bot_id, telegram_id))
        return cursor.rowcount > 0


def add_pv_verification(bot_id: int, telegram_id: int, verify_type: str, verify_url: str, status: str, result: str = "", verify_id: str = "") -> bool:
    """Add verification record."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO pv_verifications (bot_id, telegram_id, verify_type, verify_url, verify_id, status, result)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (bot_id, telegram_id, verify_type, verify_url, verify_id, status, result))
        return True


def get_pv_user_verifications(bot_id: int, telegram_id: int) -> list[dict]:
    """Get user's verification history."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM pv_verifications
            WHERE bot_id = %s AND telegram_id = %s
            ORDER BY created_at DESC
        """, (bot_id, telegram_id))
        return [dict(row) for row in cursor.fetchall()]


# Card Key Operations
def create_pv_card_key(bot_id: int, key_code: str, balance: int, created_by: int, max_uses: int = 1, expire_days: int = None) -> bool:
    """Create a redemption card key."""
    with get_cursor() as cursor:
        expire_at = None
        if expire_days:
            from datetime import timedelta
            expire_at = datetime.now() + timedelta(days=expire_days)
        
        try:
            cursor.execute("""
                INSERT INTO pv_card_keys (bot_id, key_code, balance, max_uses, created_by, expire_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (bot_id, key_code, balance, max_uses, created_by, expire_at))
            return True
        except Exception:
            return False


def use_pv_card_key(bot_id: int, key_code: str, telegram_id: int) -> int:
    """
    Use a card key. Returns:
    - positive number: balance added
    - -1: max uses reached
    - -2: expired
    - -3: already used by this user
    - None: key not found
    """
    with get_cursor() as cursor:
        # Get key info
        cursor.execute("""
            SELECT * FROM pv_card_keys WHERE bot_id = %s AND key_code = %s
        """, (bot_id, key_code))
        card = cursor.fetchone()
        
        if not card:
            return None
        
        card = dict(card)
        
        # Check expiry
        if card.get('expire_at') and datetime.now() > card['expire_at']:
            return -2
        
        # Check max uses
        if card['current_uses'] >= card['max_uses']:
            return -1
        
        # Check if user already used
        cursor.execute("""
            SELECT 1 FROM pv_card_key_usage
            WHERE bot_id = %s AND key_code = %s AND telegram_id = %s
        """, (bot_id, key_code, telegram_id))
        if cursor.fetchone():
            return -3
        
        # Use the key
        cursor.execute("""
            UPDATE pv_card_keys SET current_uses = current_uses + 1
            WHERE bot_id = %s AND key_code = %s
        """, (bot_id, key_code))
        
        cursor.execute("""
            INSERT INTO pv_card_key_usage (bot_id, key_code, telegram_id)
            VALUES (%s, %s, %s)
        """, (bot_id, key_code, telegram_id))
        
        cursor.execute("""
            UPDATE pv_users SET balance = balance + %s
            WHERE bot_id = %s AND telegram_id = %s
        """, (card['balance'], bot_id, telegram_id))
        
        return card['balance']


def get_pv_card_keys(bot_id: int) -> list[dict]:
    """Get all card keys for a bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM pv_card_keys
            WHERE bot_id = %s
            ORDER BY created_at DESC
        """, (bot_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_all_pv_user_ids(bot_id: int) -> list[int]:
    """Get all user telegram IDs for broadcast."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT telegram_id FROM pv_users WHERE bot_id = %s
        """, (bot_id,))
        return [row['telegram_id'] for row in cursor.fetchall()]


# ==================== BOT COMMANDS OPERATIONS ====================

def get_bot_command(bot_id: int, command_name: str) -> Optional[dict]:
    """Get a specific custom command for a bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, bot_id, command_name, response_text, is_enabled, created_at
            FROM bot_commands
            WHERE bot_id = %s AND command_name = %s AND is_enabled = true
        """, (bot_id, command_name))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_bot_commands(bot_id: int) -> list[dict]:
    """Get all enabled commands for a bot."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, bot_id, command_name, response_text, is_enabled, created_at
            FROM bot_commands
            WHERE bot_id = %s AND is_enabled = true
            ORDER BY command_name
        """, (bot_id,))
        return [dict(row) for row in cursor.fetchall()]
