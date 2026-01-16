"""
Database setup and models using SQLite.
"""

import sqlite3
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from config import config


@dataclass
class User:
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    is_admin: bool
    created_at: datetime


@dataclass  
class Category:
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    sort_order: int


@dataclass
class Product:
    id: int
    category_id: int
    name: str
    description: Optional[str]
    price: int
    content_type: str  # 'file', 'text', 'code'
    content: str  # file path or text content
    is_active: bool
    stock: int  # -1 = unlimited
    created_at: datetime


@dataclass
class Order:
    id: int
    order_id: str
    user_id: int
    product_id: int
    amount: int
    fee: int
    total: int
    status: str  # 'pending', 'paid', 'cancelled', 'expired'
    payment_method: str
    qris_string: Optional[str]
    expired_at: Optional[datetime]
    paid_at: Optional[datetime]
    created_at: datetime


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0
        )
    """)
    
    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            content_type TEXT NOT NULL DEFAULT 'text',
            content TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            stock INTEGER DEFAULT -1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    
    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            fee INTEGER DEFAULT 0,
            total INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT DEFAULT 'qris',
            qris_string TEXT,
            expired_at TIMESTAMP,
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


# ==================== USER OPERATIONS ====================

def get_or_create_user(telegram_id: int, username: str, first_name: str) -> User:
    """Get existing user or create new one."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    
    if row:
        user = User(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            first_name=row["first_name"],
            is_admin=bool(row["is_admin"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        )
    else:
        cursor.execute(
            "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
            (telegram_id, username, first_name)
        )
        conn.commit()
        user = User(
            id=cursor.lastrowid,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            is_admin=False,
            created_at=datetime.now()
        )
    
    conn.close()
    return user


def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Get user by Telegram ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return User(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            first_name=row["first_name"],
            is_admin=bool(row["is_admin"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        )
    return None


# ==================== CATEGORY OPERATIONS ====================

def get_active_categories() -> list[Category]:
    """Get all active categories."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, name")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        Category(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            is_active=bool(row["is_active"]),
            sort_order=row["sort_order"]
        )
        for row in rows
    ]


def get_all_categories() -> list[Category]:
    """Get all categories (including inactive)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY sort_order, name")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        Category(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            is_active=bool(row["is_active"]),
            sort_order=row["sort_order"]
        )
        for row in rows
    ]


def get_category_by_id(category_id: int) -> Optional[Category]:
    """Get category by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return Category(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            is_active=bool(row["is_active"]),
            sort_order=row["sort_order"]
        )
    return None


def create_category(name: str, description: str = None) -> Category:
    """Create a new category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO categories (name, description) VALUES (?, ?)",
        (name, description)
    )
    conn.commit()
    category_id = cursor.lastrowid
    conn.close()
    
    return Category(
        id=category_id,
        name=name,
        description=description,
        is_active=True,
        sort_order=0
    )


def update_category(category_id: int, name: str = None, description: str = None, is_active: bool = None):
    """Update a category."""
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if description is not None:
        updates.append("description = ?")
        values.append(description)
    if is_active is not None:
        updates.append("is_active = ?")
        values.append(int(is_active))
    
    if updates:
        values.append(category_id)
        cursor.execute(f"UPDATE categories SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    
    conn.close()


def delete_category(category_id: int):
    """Delete a category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


# ==================== PRODUCT OPERATIONS ====================

def get_products_by_category(category_id: int) -> list[Product]:
    """Get active products in a category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM products WHERE category_id = ? AND is_active = 1 ORDER BY name",
        (category_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [
        Product(
            id=row["id"],
            category_id=row["category_id"],
            name=row["name"],
            description=row["description"],
            price=row["price"],
            content_type=row["content_type"],
            content=row["content"],
            is_active=bool(row["is_active"]),
            stock=row["stock"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        )
        for row in rows
    ]


def get_all_products() -> list[Product]:
    """Get all products."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY category_id, name")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        Product(
            id=row["id"],
            category_id=row["category_id"],
            name=row["name"],
            description=row["description"],
            price=row["price"],
            content_type=row["content_type"],
            content=row["content"],
            is_active=bool(row["is_active"]),
            stock=row["stock"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        )
        for row in rows
    ]


def get_product_by_id(product_id: int) -> Optional[Product]:
    """Get product by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return Product(
            id=row["id"],
            category_id=row["category_id"],
            name=row["name"],
            description=row["description"],
            price=row["price"],
            content_type=row["content_type"],
            content=row["content"],
            is_active=bool(row["is_active"]),
            stock=row["stock"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        )
    return None


def create_product(
    category_id: int,
    name: str,
    price: int,
    content: str,
    content_type: str = "text",
    description: str = None,
    stock: int = -1
) -> Product:
    """Create a new product."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO products (category_id, name, description, price, content_type, content, stock)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (category_id, name, description, price, content_type, content, stock)
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    
    return Product(
        id=product_id,
        category_id=category_id,
        name=name,
        description=description,
        price=price,
        content_type=content_type,
        content=content,
        is_active=True,
        stock=stock,
        created_at=datetime.now()
    )


def update_product(product_id: int, **kwargs):
    """Update a product."""
    conn = get_connection()
    cursor = conn.cursor()
    
    allowed_fields = ["name", "description", "price", "content_type", "content", "is_active", "stock", "category_id"]
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_fields and value is not None:
            updates.append(f"{key} = ?")
            if key == "is_active":
                values.append(int(value))
            else:
                values.append(value)
    
    if updates:
        values.append(product_id)
        cursor.execute(f"UPDATE products SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    
    conn.close()


def delete_product(product_id: int):
    """Delete a product."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def decrease_stock(product_id: int):
    """Decrease product stock by 1 (if not unlimited)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET stock = stock - 1 WHERE id = ? AND stock > 0",
        (product_id,)
    )
    conn.commit()
    conn.close()


# ==================== ORDER OPERATIONS ====================

def create_order(
    order_id: str,
    user_id: int,
    product_id: int,
    amount: int,
    fee: int = 0,
    total: int = 0,
    qris_string: str = None,
    expired_at: datetime = None
) -> Order:
    """Create a new order."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO orders (order_id, user_id, product_id, amount, fee, total, qris_string, expired_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (order_id, user_id, product_id, amount, fee, total, qris_string, 
         expired_at.isoformat() if expired_at else None)
    )
    conn.commit()
    order_db_id = cursor.lastrowid
    conn.close()
    
    return Order(
        id=order_db_id,
        order_id=order_id,
        user_id=user_id,
        product_id=product_id,
        amount=amount,
        fee=fee,
        total=total,
        status="pending",
        payment_method="qris",
        qris_string=qris_string,
        expired_at=expired_at,
        paid_at=None,
        created_at=datetime.now()
    )


def get_order_by_order_id(order_id: str) -> Optional[Order]:
    """Get order by Pakasir order_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return Order(
            id=row["id"],
            order_id=row["order_id"],
            user_id=row["user_id"],
            product_id=row["product_id"],
            amount=row["amount"],
            fee=row["fee"],
            total=row["total"],
            status=row["status"],
            payment_method=row["payment_method"],
            qris_string=row["qris_string"],
            expired_at=datetime.fromisoformat(row["expired_at"]) if row["expired_at"] else None,
            paid_at=datetime.fromisoformat(row["paid_at"]) if row["paid_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        )
    return None


def get_orders_by_user(user_id: int, limit: int = 10) -> list[Order]:
    """Get orders for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [
        Order(
            id=row["id"],
            order_id=row["order_id"],
            user_id=row["user_id"],
            product_id=row["product_id"],
            amount=row["amount"],
            fee=row["fee"],
            total=row["total"],
            status=row["status"],
            payment_method=row["payment_method"],
            qris_string=row["qris_string"],
            expired_at=datetime.fromisoformat(row["expired_at"]) if row["expired_at"] else None,
            paid_at=datetime.fromisoformat(row["paid_at"]) if row["paid_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        )
        for row in rows
    ]


def get_all_orders(limit: int = 50) -> list[Order]:
    """Get all orders (for admin)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        Order(
            id=row["id"],
            order_id=row["order_id"],
            user_id=row["user_id"],
            product_id=row["product_id"],
            amount=row["amount"],
            fee=row["fee"],
            total=row["total"],
            status=row["status"],
            payment_method=row["payment_method"],
            qris_string=row["qris_string"],
            expired_at=datetime.fromisoformat(row["expired_at"]) if row["expired_at"] else None,
            paid_at=datetime.fromisoformat(row["paid_at"]) if row["paid_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now()
        )
        for row in rows
    ]


def update_order_status(order_id: str, status: str, paid_at: datetime = None):
    """Update order status."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if paid_at:
        cursor.execute(
            "UPDATE orders SET status = ?, paid_at = ? WHERE order_id = ?",
            (status, paid_at.isoformat(), order_id)
        )
    else:
        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (status, order_id)
        )
    
    conn.commit()
    conn.close()


def get_order_stats() -> dict:
    """Get order statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total orders
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    total_orders = cursor.fetchone()["count"]
    
    # Paid orders
    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'paid'")
    paid_orders = cursor.fetchone()["count"]
    
    # Total revenue
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM orders WHERE status = 'paid'")
    total_revenue = cursor.fetchone()["total"]
    
    # Today's orders
    cursor.execute(
        "SELECT COUNT(*) as count FROM orders WHERE date(created_at) = date('now')"
    )
    today_orders = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "total_revenue": total_revenue,
        "today_orders": today_orders
    }


if __name__ == "__main__":
    init_database()
