"""
Product delivery service for digital products.
"""

from telegram import Bot
from database import Product
import os


async def deliver_product(bot: Bot, chat_id: int, product: Product, order_id: str):
    """
    Deliver a digital product to the buyer.
    
    Args:
        bot: Telegram bot instance
        chat_id: User's Telegram chat ID
        product: Product to deliver
        order_id: Order ID for reference
    """
    # Send success notification first
    await bot.send_message(
        chat_id=chat_id,
        text=(
            f"✅ *Pembayaran Berhasil!*\n\n"
            f"🛒 *Pesanan:* `{order_id}`\n"
            f"📦 *Produk:* {product.name}\n\n"
            f"Berikut adalah produk Anda:"
        ),
        parse_mode="Markdown"
    )
    
    # Deliver based on content type
    if product.content_type == "file":
        await _deliver_file(bot, chat_id, product)
    elif product.content_type == "code":
        await _deliver_code(bot, chat_id, product)
    else:  # text
        await _deliver_text(bot, chat_id, product)
    
    # Send thank you message
    await bot.send_message(
        chat_id=chat_id,
        text=(
            "🙏 *Terima kasih atas pembelian Anda!*\n\n"
            "Jika ada pertanyaan, silakan hubungi admin."
        ),
        parse_mode="Markdown"
    )


async def _deliver_file(bot: Bot, chat_id: int, product: Product):
    """Deliver product as a file."""
    file_path = product.content
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            await bot.send_document(
                chat_id=chat_id,
                document=f,
                caption=f"📁 {product.name}"
            )
    else:
        # If file doesn't exist, send path as text
        await bot.send_message(
            chat_id=chat_id,
            text=f"📥 *Download Link:*\n{product.content}",
            parse_mode="Markdown"
        )


async def _deliver_text(bot: Bot, chat_id: int, product: Product):
    """Deliver product as text message."""
    # Split long messages if needed (Telegram limit is 4096 chars)
    content = product.content
    max_length = 4000
    
    if len(content) <= max_length:
        await bot.send_message(
            chat_id=chat_id,
            text=f"📝 *{product.name}*\n\n{content}",
            parse_mode="Markdown"
        )
    else:
        # Split into multiple messages
        parts = [content[i:i+max_length] for i in range(0, len(content), max_length)]
        for i, part in enumerate(parts, 1):
            await bot.send_message(
                chat_id=chat_id,
                text=f"📝 *{product.name}* (Part {i}/{len(parts)})\n\n{part}",
                parse_mode="Markdown"
            )


async def _deliver_code(bot: Bot, chat_id: int, product: Product):
    """Deliver product as code block."""
    content = product.content
    
    # Send as code block
    await bot.send_message(
        chat_id=chat_id,
        text=f"💻 *{product.name}*\n\n```\n{content}\n```",
        parse_mode="Markdown"
    )
