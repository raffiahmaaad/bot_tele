"""
Keyboard helper utilities for Telegram inline keyboards.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Tuple


def create_menu_keyboard(categories: list = None, balance: int = 0) -> InlineKeyboardMarkup:
    """Create main menu keyboard with ChenStore-style category buttons."""
    keyboard = []
    
    # Category buttons in grid (3 per row) - like ChenStore
    if categories:
        row = []
        for i, cat in enumerate(categories):
            row.append(InlineKeyboardButton(cat['name'], callback_data=f"cat_{cat['id']}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:  # Add remaining buttons
            keyboard.append(row)
    
    # Menu buttons row
    keyboard.append([
        InlineKeyboardButton("📂 Uncategory", callback_data="menu_uncategory"),
        InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard"),
        InlineKeyboardButton("📦 Semua Produk", callback_data="menu_all_products"),
    ])
    
    # Balance and deposit row
    balance_str = f"Rp {balance:,}".replace(",", ".")
    keyboard.append([
        InlineKeyboardButton(f"💰 Saldo: {balance_str}", callback_data="menu_balance"),
        InlineKeyboardButton("➕ Deposit", callback_data="menu_deposit"),
    ])
    
    # Bottom row
    keyboard.append([
        InlineKeyboardButton("📋 Pesanan Saya", callback_data="menu_orders"),
        InlineKeyboardButton("ℹ️ Bantuan", callback_data="menu_help"),
    ])
    
    return InlineKeyboardMarkup(keyboard)


def create_admin_menu_keyboard(categories: list = None, balance: int = 0) -> InlineKeyboardMarkup:
    """Create admin menu keyboard with ChenStore-style + admin panel."""
    keyboard = []
    
    # Category buttons in grid (3 per row)
    if categories:
        row = []
        for i, cat in enumerate(categories):
            row.append(InlineKeyboardButton(cat['name'], callback_data=f"cat_{cat['id']}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
    
    # Menu buttons row
    keyboard.append([
        InlineKeyboardButton("📂 Uncategory", callback_data="menu_uncategory"),
        InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard"),
        InlineKeyboardButton("📦 Semua Produk", callback_data="menu_all_products"),
    ])
    
    # Balance and deposit row
    balance_str = f"Rp {balance:,}".replace(",", ".")
    keyboard.append([
        InlineKeyboardButton(f"💰 Saldo: {balance_str}", callback_data="menu_balance"),
        InlineKeyboardButton("➕ Deposit", callback_data="menu_deposit"),
    ])
    
    # Bottom row
    keyboard.append([
        InlineKeyboardButton("📋 Pesanan Saya", callback_data="menu_orders"),
        InlineKeyboardButton("ℹ️ Bantuan", callback_data="menu_help"),
    ])
    
    # Admin panel
    keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_menu")])
    
    return InlineKeyboardMarkup(keyboard)


def create_category_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Create keyboard for category selection."""
    keyboard = []
    
    # Add categories in pairs
    for i in range(0, len(categories), 2):
        row = [InlineKeyboardButton(
            f"📁 {categories[i].name}",
            callback_data=f"cat_{categories[i].id}"
        )]
        if i + 1 < len(categories):
            row.append(InlineKeyboardButton(
                f"📁 {categories[i+1].name}",
                callback_data=f"cat_{categories[i+1].id}"
            ))
        keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")])
    
    return InlineKeyboardMarkup(keyboard)


def create_product_keyboard(products: list, category_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for product selection."""
    keyboard = []
    
    for product in products:
        # Format price
        price_str = f"Rp {product.price:,}".replace(",", ".")
        keyboard.append([
            InlineKeyboardButton(
                f"🛍️ {product.name} - {price_str}",
                callback_data=f"prod_{product.id}"
            )
        ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Kembali ke Kategori", callback_data="menu_catalog")])
    
    return InlineKeyboardMarkup(keyboard)


def create_product_detail_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for product detail view."""
    keyboard = [
        [InlineKeyboardButton("🛒 Beli Sekarang", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton("🔙 Kembali", callback_data=f"cat_{category_id}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_confirm_purchase_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for purchase confirmation."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Ya, Bayar", callback_data=f"confirm_buy_{product_id}"),
            InlineKeyboardButton("❌ Batal", callback_data=f"prod_{product_id}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_payment_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Create keyboard for payment status."""
    keyboard = [
        [InlineKeyboardButton("🔄 Cek Status", callback_data=f"check_{order_id}")],
        [InlineKeyboardButton("❌ Batalkan", callback_data=f"cancel_{order_id}")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_order_keyboard(order_id: str, status: str) -> InlineKeyboardMarkup:
    """Create keyboard for order detail."""
    keyboard = []
    
    if status == "pending":
        keyboard.append([
            InlineKeyboardButton("🔄 Cek Status", callback_data=f"check_{order_id}")
        ])
        keyboard.append([
            InlineKeyboardButton("❌ Batalkan", callback_data=f"cancel_{order_id}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 Kembali", callback_data="menu_orders")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def create_back_keyboard(callback_data: str = "back_menu") -> InlineKeyboardMarkup:
    """Create simple back button keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Kembali", callback_data=callback_data)]
    ])


# ==================== ADMIN KEYBOARDS ====================

def create_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Create admin panel keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📁 Kelola Kategori", callback_data="admin_categories"),
            InlineKeyboardButton("📦 Kelola Produk", callback_data="admin_products"),
        ],
        [
            InlineKeyboardButton("📋 Semua Pesanan", callback_data="admin_orders"),
            InlineKeyboardButton("📊 Statistik", callback_data="admin_stats"),
        ],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_admin_categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Create admin categories management keyboard."""
    keyboard = []
    
    for cat in categories:
        status = "✅" if cat.is_active else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {cat.name}",
                callback_data=f"admin_cat_{cat.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("➕ Tambah Kategori", callback_data="admin_cat_add")
    ])
    keyboard.append([
        InlineKeyboardButton("🔙 Kembali", callback_data="admin_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def create_admin_category_detail_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for admin category detail."""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"admin_cat_edit_{category_id}"),
            InlineKeyboardButton("🗑️ Hapus", callback_data=f"admin_cat_del_{category_id}"),
        ],
        [
            InlineKeyboardButton("🔄 Toggle Aktif", callback_data=f"admin_cat_toggle_{category_id}"),
        ],
        [InlineKeyboardButton("🔙 Kembali", callback_data="admin_categories")],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_admin_products_keyboard(products: list) -> InlineKeyboardMarkup:
    """Create admin products management keyboard."""
    keyboard = []
    
    for prod in products:
        status = "✅" if prod.is_active else "❌"
        price_str = f"Rp {prod.price:,}".replace(",", ".")
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {prod.name} ({price_str})",
                callback_data=f"admin_prod_{prod.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("➕ Tambah Produk", callback_data="admin_prod_add")
    ])
    keyboard.append([
        InlineKeyboardButton("🔙 Kembali", callback_data="admin_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def create_admin_product_detail_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for admin product detail."""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"admin_prod_edit_{product_id}"),
            InlineKeyboardButton("🗑️ Hapus", callback_data=f"admin_prod_del_{product_id}"),
        ],
        [
            InlineKeyboardButton("🔄 Toggle Aktif", callback_data=f"admin_prod_toggle_{product_id}"),
        ],
        [InlineKeyboardButton("🔙 Kembali", callback_data="admin_products")],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_cancel_keyboard() -> InlineKeyboardMarkup:
    """Create cancel keyboard for conversation handlers."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Batal", callback_data="admin_cancel")]
    ])


def create_category_select_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Create keyboard for selecting category when adding product."""
    keyboard = []
    
    for cat in categories:
        keyboard.append([
            InlineKeyboardButton(
                f"📁 {cat.name}",
                callback_data=f"select_cat_{cat.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("❌ Batal", callback_data="admin_cancel")
    ])
    
    return InlineKeyboardMarkup(keyboard)
