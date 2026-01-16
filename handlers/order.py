"""
Handler for orders, payments, and checkout.
"""

import uuid
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from config import config
from database import (
    get_product_by_id,
    get_user_by_telegram_id,
    create_order,
    get_order_by_order_id,
    get_orders_by_user,
    update_order_status,
    decrease_stock
)
from services.pakasir import pakasir_client
from utils.qr_generator import generate_qr_image
from utils.keyboard import (
    create_confirm_purchase_keyboard,
    create_payment_keyboard,
    create_order_keyboard,
    create_back_keyboard
)


def generate_order_id() -> str:
    """Generate unique order ID."""
    timestamp = datetime.now().strftime("%y%m%d")
    unique = uuid.uuid4().hex[:6].upper()
    return f"ORD{timestamp}{unique}"


async def show_buy_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show purchase confirmation."""
    query = update.callback_query
    await query.answer()
    
    # Extract product ID
    product_id = int(query.data.split("_")[1])
    product = get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text("❌ Produk tidak ditemukan.")
        return
    
    if product.stock == 0:
        await query.edit_message_text(
            "❌ Maaf, stok produk habis.",
            reply_markup=create_back_keyboard(f"cat_{product.category_id}")
        )
        return
    
    # Format price
    price_str = f"Rp {product.price:,}".replace(",", ".")
    
    text = (
        f"🛒 *Konfirmasi Pembelian*\n\n"
        f"📦 *Produk:* {product.name}\n"
        f"💰 *Harga:* {price_str}\n\n"
        f"_Biaya tambahan dari payment gateway akan ditampilkan saat pembayaran._\n\n"
        f"Lanjutkan pembayaran?"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_confirm_purchase_keyboard(product_id)
    )


async def process_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process purchase and generate QRIS."""
    query = update.callback_query
    await query.answer("⏳ Memproses pembayaran...")
    
    # Extract product ID
    product_id = int(query.data.split("_")[2])  # confirm_buy_<id>
    product = get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text("❌ Produk tidak ditemukan.")
        return
    
    # Get user
    user = get_user_by_telegram_id(update.effective_user.id)
    if not user:
        await query.edit_message_text("❌ User tidak ditemukan. Silakan /start ulang.")
        return
    
    # Generate unique order ID
    order_id = generate_order_id()
    
    # Show processing message
    await query.edit_message_text(
        "⏳ *Membuat pembayaran QRIS...*\n\nMohon tunggu sebentar.",
        parse_mode="Markdown"
    )
    
    # Create transaction via Pakasir
    payment = await pakasir_client.create_transaction(
        order_id=order_id,
        amount=product.price
    )
    
    if not payment:
        await query.edit_message_text(
            "❌ *Gagal membuat pembayaran*\n\n"
            "Terjadi kesalahan saat menghubungi payment gateway. "
            "Silakan coba lagi nanti.",
            parse_mode="Markdown",
            reply_markup=create_back_keyboard(f"prod_{product_id}")
        )
        return
    
    # Parse expired_at
    try:
        expired_at = datetime.fromisoformat(payment.expired_at.replace("Z", "+00:00"))
    except:
        expired_at = None
    
    # Save order to database
    order = create_order(
        order_id=order_id,
        user_id=user.id,
        product_id=product_id,
        amount=product.price,
        fee=payment.fee,
        total=payment.total_payment,
        qris_string=payment.payment_number,
        expired_at=expired_at
    )
    
    # Generate QR code image
    qr_image = generate_qr_image(payment.payment_number)
    
    # Format amounts
    amount_str = f"Rp {product.price:,}".replace(",", ".")
    fee_str = f"Rp {payment.fee:,}".replace(",", ".")
    total_str = f"Rp {payment.total_payment:,}".replace(",", ".")
    
    # Create payment message
    payment_text = (
        f"💳 *Pembayaran QRIS*\n\n"
        f"🆔 *Order:* `{order_id}`\n"
        f"📦 *Produk:* {product.name}\n\n"
        f"💰 *Harga:* {amount_str}\n"
        f"📋 *Biaya Admin:* {fee_str}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💵 *Total Bayar:* {total_str}\n\n"
        f"📱 *Scan QR di bawah dengan aplikasi e-wallet atau mobile banking Anda*\n\n"
        f"⏰ *Berlaku hingga:* {expired_at.strftime('%H:%M WIB') if expired_at else 'N/A'}\n\n"
        f"_Setelah pembayaran berhasil, produk akan dikirim otomatis._"
    )
    
    # Delete previous message
    await query.delete_message()
    
    # Send QR code as photo
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=qr_image,
        caption=payment_text,
        parse_mode="Markdown",
        reply_markup=create_payment_keyboard(order_id)
    )


async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check payment status manually."""
    query = update.callback_query
    await query.answer("🔄 Memeriksa status...")
    
    # Extract order ID
    order_id = query.data.split("_")[1]  # check_<order_id>
    
    order = get_order_by_order_id(order_id)
    
    if not order:
        await query.message.reply_text("❌ Order tidak ditemukan.")
        return
    
    if order.status == "paid":
        await query.message.reply_text(
            f"✅ *Pembayaran Sudah Berhasil!*\n\n"
            f"Order `{order_id}` sudah terbayar dan produk sudah dikirim.",
            parse_mode="Markdown"
        )
        return
    
    # Check status from Pakasir
    status = await pakasir_client.get_transaction_status(order_id, order.amount)
    
    if status and status.status == "completed":
        # Update order status
        update_order_status(order_id, "paid", datetime.now())
        decrease_stock(order.product_id)
        
        # Deliver product
        from services.delivery import deliver_product
        product = get_product_by_id(order.product_id)
        user = get_user_by_telegram_id(update.effective_user.id)
        
        await deliver_product(
            context.bot,
            update.effective_chat.id,
            product,
            order_id
        )
    else:
        await query.message.reply_text(
            f"⏳ *Pembayaran Belum Diterima*\n\n"
            f"Order `{order_id}` masih menunggu pembayaran.\n"
            f"Silakan scan QRIS dan selesaikan pembayaran.",
            parse_mode="Markdown"
        )


async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel a pending payment."""
    query = update.callback_query
    await query.answer()
    
    # Extract order ID
    order_id = query.data.split("_")[1]  # cancel_<order_id>
    
    order = get_order_by_order_id(order_id)
    
    if not order:
        await query.message.reply_text("❌ Order tidak ditemukan.")
        return
    
    if order.status != "pending":
        await query.message.reply_text(
            f"⚠️ Order `{order_id}` tidak dapat dibatalkan (status: {order.status})",
            parse_mode="Markdown"
        )
        return
    
    # Cancel on Pakasir
    await pakasir_client.cancel_transaction(order_id, order.amount)
    
    # Update local status
    update_order_status(order_id, "cancelled")
    
    await query.message.reply_text(
        f"✅ *Order Dibatalkan*\n\n"
        f"Order `{order_id}` telah dibatalkan.",
        parse_mode="Markdown",
        reply_markup=create_back_keyboard()
    )


async def show_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's order history."""
    query = update.callback_query
    await query.answer()
    
    user = get_user_by_telegram_id(update.effective_user.id)
    
    if not user:
        await query.edit_message_text(
            "❌ User tidak ditemukan. Silakan /start.",
            reply_markup=create_back_keyboard()
        )
        return
    
    orders = get_orders_by_user(user.id)
    
    if not orders:
        await query.edit_message_text(
            "📋 *Pesanan Saya*\n\n📭 Anda belum memiliki pesanan.",
            parse_mode="Markdown",
            reply_markup=create_back_keyboard()
        )
        return
    
    text = "📋 *Pesanan Saya*\n\n"
    
    status_emoji = {
        "pending": "⏳",
        "paid": "✅",
        "cancelled": "❌",
        "expired": "⌛"
    }
    
    for order in orders[:10]:  # Show last 10 orders
        product = get_product_by_id(order.product_id)
        product_name = product.name if product else "Unknown"
        emoji = status_emoji.get(order.status, "❓")
        amount_str = f"Rp {order.amount:,}".replace(",", ".")
        date_str = order.created_at.strftime("%d/%m/%Y")
        
        text += f"{emoji} `{order.order_id}`\n"
        text += f"   📦 {product_name}\n"
        text += f"   💰 {amount_str} | {date_str}\n\n"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_back_keyboard()
    )


def get_order_handlers():
    """Get all handlers for order module."""
    return [
        CallbackQueryHandler(show_buy_confirmation, pattern="^buy_\\d+$"),
        CallbackQueryHandler(process_purchase, pattern="^confirm_buy_\\d+$"),
        CallbackQueryHandler(check_payment_status, pattern="^check_[A-Z0-9]+$"),
        CallbackQueryHandler(cancel_payment, pattern="^cancel_[A-Z0-9]+$"),
        CallbackQueryHandler(show_my_orders, pattern="^menu_orders$"),
    ]
