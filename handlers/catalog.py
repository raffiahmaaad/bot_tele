"""
Handler for catalog browsing and product display.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from database import (
    get_active_categories,
    get_products_by_category,
    get_product_by_id,
    get_category_by_id
)
from utils.keyboard import (
    create_category_keyboard,
    create_product_keyboard,
    create_product_detail_keyboard
)


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show catalog categories."""
    query = update.callback_query
    await query.answer()
    
    categories = get_active_categories()
    
    if not categories:
        await query.edit_message_text(
            "📭 *Katalog Kosong*\n\nBelum ada kategori produk tersedia.",
            parse_mode="Markdown",
            reply_markup=create_category_keyboard([])
        )
        return
    
    text = (
        "📦 *Katalog Produk*\n\n"
        "Pilih kategori di bawah ini:"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_category_keyboard(categories)
    )


async def show_category_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show products in a category."""
    query = update.callback_query
    await query.answer()
    
    # Extract category ID from callback data
    category_id = int(query.data.split("_")[1])
    
    category = get_category_by_id(category_id)
    products = get_products_by_category(category_id)
    
    if not products:
        text = f"📁 *{category.name}*\n\n📭 Tidak ada produk dalam kategori ini."
    else:
        text = (
            f"📁 *{category.name}*\n"
            f"{category.description or ''}\n\n"
            f"📦 *{len(products)} produk tersedia:*"
        )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_product_keyboard(products, category_id)
    )


async def show_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show product detail."""
    query = update.callback_query
    await query.answer()
    
    # Extract product ID from callback data
    product_id = int(query.data.split("_")[1])
    
    product = get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text(
            "❌ Produk tidak ditemukan.",
            parse_mode="Markdown"
        )
        return
    
    # Format price
    price_str = f"Rp {product.price:,}".replace(",", ".")
    
    # Stock info
    if product.stock == -1:
        stock_str = "Unlimited"
    elif product.stock > 0:
        stock_str = f"{product.stock} tersedia"
    else:
        stock_str = "❌ Stok habis"
    
    text = (
        f"🛍️ *{product.name}*\n\n"
        f"{product.description or 'Tidak ada deskripsi.'}\n\n"
        f"💰 *Harga:* {price_str}\n"
        f"📦 *Stok:* {stock_str}\n"
        f"📂 *Tipe:* {product.content_type.capitalize()}"
    )
    
    # Check if product is available
    if product.stock == 0:
        from utils.keyboard import create_back_keyboard
        await query.edit_message_text(
            text + "\n\n⚠️ *Maaf, produk ini sedang tidak tersedia.*",
            parse_mode="Markdown",
            reply_markup=create_back_keyboard(f"cat_{product.category_id}")
        )
        return
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_product_detail_keyboard(product_id, product.category_id)
    )


def get_catalog_handlers():
    """Get all handlers for catalog module."""
    return [
        CallbackQueryHandler(show_catalog, pattern="^menu_catalog$"),
        CallbackQueryHandler(show_category_products, pattern="^cat_\\d+$"),
        CallbackQueryHandler(show_product_detail, pattern="^prod_\\d+$"),
    ]
