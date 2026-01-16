"""
Handler for admin panel functionality.
"""

from telegram import Update
from telegram.ext import (
    ContextTypes, 
    CallbackQueryHandler, 
    ConversationHandler,
    MessageHandler,
    filters
)

from config import config
from database import (
    get_all_categories,
    get_category_by_id,
    create_category,
    update_category,
    delete_category,
    get_all_products,
    get_product_by_id,
    create_product,
    update_product,
    delete_product,
    get_all_orders,
    get_order_stats,
    get_user_by_telegram_id
)
from utils.keyboard import (
    create_admin_panel_keyboard,
    create_admin_categories_keyboard,
    create_admin_category_detail_keyboard,
    create_admin_products_keyboard,
    create_admin_product_detail_keyboard,
    create_cancel_keyboard,
    create_category_select_keyboard,
    create_back_keyboard
)


# Conversation states
(
    CAT_NAME, CAT_DESC,
    PROD_NAME, PROD_DESC, PROD_PRICE, PROD_CONTENT, PROD_CATEGORY
) = range(7)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in config.ADMIN_TELEGRAM_IDS


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel menu."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        await query.edit_message_text("❌ Akses ditolak. Anda bukan admin.")
        return
    
    text = (
        "⚙️ *Admin Panel*\n\n"
        "Kelola produk, kategori, dan lihat statistik toko."
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_admin_panel_keyboard()
    )


# ==================== CATEGORY MANAGEMENT ====================

async def admin_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show category management."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    categories = get_all_categories()
    
    text = (
        "📁 *Kelola Kategori*\n\n"
        f"Total: {len(categories)} kategori\n"
        "Pilih kategori untuk mengelola:"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_admin_categories_keyboard(categories)
    )


async def admin_category_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show category detail for admin."""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[2])  # admin_cat_<id>
    category = get_category_by_id(category_id)
    
    if not category:
        await query.edit_message_text("❌ Kategori tidak ditemukan.")
        return
    
    status = "✅ Aktif" if category.is_active else "❌ Nonaktif"
    
    text = (
        f"📁 *Detail Kategori*\n\n"
        f"*Nama:* {category.name}\n"
        f"*Deskripsi:* {category.description or '-'}\n"
        f"*Status:* {status}\n"
        f"*Urutan:* {category.sort_order}"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_admin_category_detail_keyboard(category_id)
    )


async def admin_category_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle category active status."""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[3])  # admin_cat_toggle_<id>
    category = get_category_by_id(category_id)
    
    if category:
        update_category(category_id, is_active=not category.is_active)
        status = "dinonaktifkan" if category.is_active else "diaktifkan"
        await query.answer(f"✅ Kategori {status}")
    
    # Refresh detail
    await admin_category_detail(update, context)


async def admin_category_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a category."""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[3])  # admin_cat_del_<id>
    category = get_category_by_id(category_id)
    
    if category:
        delete_category(category_id)
        await query.answer(f"🗑️ Kategori '{category.name}' dihapus")
    
    # Go back to category list
    await admin_categories(update, context)


async def admin_category_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding new category."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    await query.edit_message_text(
        "📁 *Tambah Kategori Baru*\n\n"
        "Masukkan nama kategori:",
        parse_mode="Markdown",
        reply_markup=create_cancel_keyboard()
    )
    
    return CAT_NAME


async def admin_category_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive category name."""
    context.user_data["new_category_name"] = update.message.text
    
    await update.message.reply_text(
        "📝 Masukkan deskripsi kategori (atau ketik '-' untuk skip):",
        reply_markup=create_cancel_keyboard()
    )
    
    return CAT_DESC


async def admin_category_add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive category description and create category."""
    name = context.user_data.get("new_category_name")
    desc = update.message.text if update.message.text != "-" else None
    
    category = create_category(name, desc)
    
    await update.message.reply_text(
        f"✅ *Kategori Berhasil Ditambahkan!*\n\n"
        f"*Nama:* {category.name}\n"
        f"*Deskripsi:* {category.description or '-'}",
        parse_mode="Markdown",
        reply_markup=create_back_keyboard("admin_categories")
    )
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END


# ==================== PRODUCT MANAGEMENT ====================

async def admin_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show product management."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    products = get_all_products()
    
    text = (
        "📦 *Kelola Produk*\n\n"
        f"Total: {len(products)} produk\n"
        "Pilih produk untuk mengelola:"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_admin_products_keyboard(products)
    )


async def admin_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show product detail for admin."""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split("_")[2])  # admin_prod_<id>
    product = get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text("❌ Produk tidak ditemukan.")
        return
    
    status = "✅ Aktif" if product.is_active else "❌ Nonaktif"
    price_str = f"Rp {product.price:,}".replace(",", ".")
    stock_str = "Unlimited" if product.stock == -1 else str(product.stock)
    
    # Truncate content for display
    content_preview = product.content[:100] + "..." if len(product.content) > 100 else product.content
    
    category = get_category_by_id(product.category_id)
    cat_name = category.name if category else "Unknown"
    
    text = (
        f"📦 *Detail Produk*\n\n"
        f"*Nama:* {product.name}\n"
        f"*Kategori:* {cat_name}\n"
        f"*Deskripsi:* {product.description or '-'}\n"
        f"*Harga:* {price_str}\n"
        f"*Stok:* {stock_str}\n"
        f"*Tipe:* {product.content_type}\n"
        f"*Status:* {status}\n\n"
        f"*Content Preview:*\n`{content_preview}`"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_admin_product_detail_keyboard(product_id)
    )


async def admin_product_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle product active status."""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split("_")[3])  # admin_prod_toggle_<id>
    product = get_product_by_id(product_id)
    
    if product:
        update_product(product_id, is_active=not product.is_active)
        status = "dinonaktifkan" if product.is_active else "diaktifkan"
        await query.answer(f"✅ Produk {status}")
    
    # Refresh detail
    await admin_product_detail(update, context)


async def admin_product_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a product."""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split("_")[3])  # admin_prod_del_<id>
    product = get_product_by_id(product_id)
    
    if product:
        delete_product(product_id)
        await query.answer(f"🗑️ Produk '{product.name}' dihapus")
    
    # Go back to product list
    await admin_products(update, context)


async def admin_product_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding new product."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    categories = get_all_categories()
    
    if not categories:
        await query.edit_message_text(
            "❌ Tidak ada kategori. Buat kategori terlebih dahulu.",
            reply_markup=create_back_keyboard("admin_menu")
        )
        return ConversationHandler.END
    
    await query.edit_message_text(
        "📦 *Tambah Produk Baru*\n\n"
        "Pilih kategori untuk produk:",
        parse_mode="Markdown",
        reply_markup=create_category_select_keyboard(categories)
    )
    
    return PROD_CATEGORY


async def admin_product_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive category selection for new product."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_cancel":
        await admin_products(update, context)
        return ConversationHandler.END
    
    category_id = int(query.data.split("_")[2])  # select_cat_<id>
    context.user_data["new_product_category"] = category_id
    
    await query.edit_message_text(
        "📝 Masukkan nama produk:",
        reply_markup=create_cancel_keyboard()
    )
    
    return PROD_NAME


async def admin_product_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive product name."""
    context.user_data["new_product_name"] = update.message.text
    
    await update.message.reply_text(
        "📝 Masukkan deskripsi produk (atau ketik '-' untuk skip):",
        reply_markup=create_cancel_keyboard()
    )
    
    return PROD_DESC


async def admin_product_add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive product description."""
    context.user_data["new_product_desc"] = update.message.text if update.message.text != "-" else None
    
    await update.message.reply_text(
        "💰 Masukkan harga produk (angka saja, contoh: 50000):",
        reply_markup=create_cancel_keyboard()
    )
    
    return PROD_PRICE


async def admin_product_add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive product price."""
    try:
        price = int(update.message.text.replace(".", "").replace(",", ""))
        context.user_data["new_product_price"] = price
    except ValueError:
        await update.message.reply_text(
            "❌ Format harga tidak valid. Masukkan angka saja:",
            reply_markup=create_cancel_keyboard()
        )
        return PROD_PRICE
    
    await update.message.reply_text(
        "📄 Masukkan konten produk digital:\n"
        "(Bisa berupa teks, kode, link download, dll)",
        reply_markup=create_cancel_keyboard()
    )
    
    return PROD_CONTENT


async def admin_product_add_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive product content and create product."""
    content = update.message.text
    
    # Determine content type
    content_type = "text"
    if content.startswith("http://") or content.startswith("https://"):
        content_type = "file"  # URL/link
    elif "```" in content or len(content.split("\n")) > 5:
        content_type = "code"  # Code block
    
    product = create_product(
        category_id=context.user_data["new_product_category"],
        name=context.user_data["new_product_name"],
        price=context.user_data["new_product_price"],
        content=content,
        content_type=content_type,
        description=context.user_data.get("new_product_desc")
    )
    
    price_str = f"Rp {product.price:,}".replace(",", ".")
    
    await update.message.reply_text(
        f"✅ *Produk Berhasil Ditambahkan!*\n\n"
        f"*Nama:* {product.name}\n"
        f"*Harga:* {price_str}\n"
        f"*Tipe:* {product.content_type}",
        parse_mode="Markdown",
        reply_markup=create_back_keyboard("admin_products")
    )
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current admin operation."""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await admin_menu(update, context)
    return ConversationHandler.END


# ==================== ORDERS & STATS ====================

async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all orders for admin."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    orders = get_all_orders(limit=20)
    
    if not orders:
        await query.edit_message_text(
            "📋 *Semua Pesanan*\n\n📭 Belum ada pesanan.",
            parse_mode="Markdown",
            reply_markup=create_back_keyboard("admin_menu")
        )
        return
    
    text = "📋 *Semua Pesanan* (20 terbaru)\n\n"
    
    status_emoji = {
        "pending": "⏳",
        "paid": "✅",
        "cancelled": "❌",
        "expired": "⌛"
    }
    
    for order in orders:
        product = get_product_by_id(order.product_id)
        product_name = product.name if product else "Unknown"
        emoji = status_emoji.get(order.status, "❓")
        amount_str = f"Rp {order.amount:,}".replace(",", ".")
        date_str = order.created_at.strftime("%d/%m %H:%M")
        
        text += f"{emoji} `{order.order_id}`\n"
        text += f"   📦 {product_name} | {amount_str}\n"
        text += f"   📅 {date_str}\n\n"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_back_keyboard("admin_menu")
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show store statistics."""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(update.effective_user.id):
        return
    
    stats = get_order_stats()
    
    revenue_str = f"Rp {stats['total_revenue']:,}".replace(",", ".")
    
    text = (
        "📊 *Statistik Toko*\n\n"
        f"📦 *Total Pesanan:* {stats['total_orders']}\n"
        f"✅ *Pesanan Sukses:* {stats['paid_orders']}\n"
        f"💰 *Total Pendapatan:* {revenue_str}\n"
        f"📅 *Pesanan Hari Ini:* {stats['today_orders']}"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_back_keyboard("admin_menu")
    )


def get_admin_handlers():
    """Get all handlers for admin module."""
    # Category conversation handler
    category_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_category_add_start, pattern="^admin_cat_add$")
        ],
        states={
            CAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_category_add_name)],
            CAT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_category_add_desc)],
        },
        fallbacks=[
            CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$")
        ],
        allow_reentry=True
    )
    
    # Product conversation handler
    product_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_product_add_start, pattern="^admin_prod_add$")
        ],
        states={
            PROD_CATEGORY: [
                CallbackQueryHandler(admin_product_select_category, pattern="^select_cat_\\d+$"),
                CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$")
            ],
            PROD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product_add_name)],
            PROD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product_add_desc)],
            PROD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product_add_price)],
            PROD_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product_add_content)],
        },
        fallbacks=[
            CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$")
        ],
        allow_reentry=True
    )
    
    return [
        category_conv_handler,
        product_conv_handler,
        CallbackQueryHandler(admin_menu, pattern="^admin_menu$"),
        CallbackQueryHandler(admin_categories, pattern="^admin_categories$"),
        CallbackQueryHandler(admin_category_detail, pattern="^admin_cat_\\d+$"),
        CallbackQueryHandler(admin_category_toggle, pattern="^admin_cat_toggle_\\d+$"),
        CallbackQueryHandler(admin_category_delete, pattern="^admin_cat_del_\\d+$"),
        CallbackQueryHandler(admin_products, pattern="^admin_products$"),
        CallbackQueryHandler(admin_product_detail, pattern="^admin_prod_\\d+$"),
        CallbackQueryHandler(admin_product_toggle, pattern="^admin_prod_toggle_\\d+$"),
        CallbackQueryHandler(admin_product_delete, pattern="^admin_prod_del_\\d+$"),
        CallbackQueryHandler(admin_orders, pattern="^admin_orders$"),
        CallbackQueryHandler(admin_stats, pattern="^admin_stats$"),
    ]
