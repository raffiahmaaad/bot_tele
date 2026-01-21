"""
Product delivery service for digital products.
Uses stock content from database_pg.
"""

from telegram import Bot
import os


async def deliver_product(bot: Bot, chat_id: int, stock_content: str, product_name: str, order_id: str):
    """
    Deliver a digital product to the buyer.
    
    Args:
        bot: Telegram bot instance
        chat_id: User's Telegram chat ID
        stock_content: The stock content/credential to deliver
        product_name: Product name for display
        order_id: Order ID for reference
    """
    # Send success notification first
    await bot.send_message(
        chat_id=chat_id,
        text=(
            f"✅ *Pembayaran Berhasil!*\n\n"
            f"🛒 *Pesanan:* `{order_id}`\n"
            f"📦 *Produk:* {product_name}\n\n"
            f"Berikut adalah produk Anda:"
        ),
        parse_mode="Markdown"
    )
    
    # Deliver the stock content
    await _deliver_content(bot, chat_id, stock_content, product_name)
    
    # Send thank you message
    await bot.send_message(
        chat_id=chat_id,
        text=(
            "🙏 *Terima kasih atas pembelian Anda!*\n\n"
            "Jika ada pertanyaan, silakan hubungi admin."
        ),
        parse_mode="Markdown"
    )


async def _deliver_content(bot: Bot, chat_id: int, content: str, product_name: str):
    """Deliver content as text message."""
    # Split long messages if needed (Telegram limit is 4096 chars)
    max_length = 4000
    
    if len(content) <= max_length:
        await bot.send_message(
            chat_id=chat_id,
            text=f"📝 *{product_name}*\n\n`{content}`",
            parse_mode="Markdown"
        )
    else:
        # Split into multiple messages
        parts = [content[i:i+max_length] for i in range(0, len(content), max_length)]
        for i, part in enumerate(parts, 1):
            await bot.send_message(
                chat_id=chat_id,
                text=f"📝 *{product_name}* (Part {i}/{len(parts)})\n\n`{part}`",
                parse_mode="Markdown"
            )
