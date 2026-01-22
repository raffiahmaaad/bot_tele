"""
Store Bot - Deposit Handler.
Handles deposit balance via QRIS Pakasir.
"""

import uuid
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database_pg import (
    get_bot_user,
    create_deposit,
    get_deposit_by_order_id,
    update_deposit_status,
    add_user_balance,
    get_user_balance
)
from services.pakasir import PakasirClient
from utils.qr_generator import generate_qr_image
from utils.keyboard import create_back_keyboard


# Deposit amount options
DEPOSIT_AMOUNTS = [10000, 25000, 50000, 100000, 250000, 500000]


def generate_deposit_id() -> str:
    """Generate unique deposit order ID."""
    timestamp = datetime.now().strftime("%y%m%d")
    unique = uuid.uuid4().hex[:6].upper()
    return f"DEP{timestamp}{unique}"


async def show_deposit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show deposit amount options."""
    query = update.callback_query
    await query.answer()
    
    bot_id = context.bot_data.get('bot_id')
    user = update.effective_user
    balance = get_user_balance(bot_id, user.id)
    balance_str = f"Rp {balance:,}".replace(",", ".")
    
    text = (
        f"➕ *Deposit Saldo*\n\n"
        f"💰 *Saldo saat ini:* {balance_str}\n\n"
        f"Pilih nominal deposit:"
    )
    
    # Create amount buttons in 2 columns
    keyboard = []
    row = []
    for amount in DEPOSIT_AMOUNTS:
        amount_str = f"Rp {amount:,}".replace(",", ".")
        row.append(InlineKeyboardButton(amount_str, callback_data=f"deposit_{amount}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")])
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def process_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process deposit and generate QRIS."""
    query = update.callback_query
    await query.answer("⏳ Membuat QRIS deposit...")
    
    bot_id = context.bot_data.get('bot_id')
    pakasir_slug = context.bot_data.get('pakasir_slug')
    pakasir_api_key = context.bot_data.get('pakasir_api_key')
    user = update.effective_user
    
    # Extract amount from callback
    amount = int(query.data.split("_")[1])
    
    # Generate deposit order ID
    order_id = generate_deposit_id()
    
    # Show processing message
    await query.edit_message_text(
        "⏳ *Membuat pembayaran QRIS...*\n\nMohon tunggu sebentar.",
        parse_mode="Markdown"
    )
    
    # Create Pakasir transaction
    pakasir = PakasirClient(pakasir_slug, pakasir_api_key)
    payment = await pakasir.create_transaction(
        order_id=order_id,
        amount=amount
    )
    
    if not payment:
        await query.edit_message_text(
            "❌ *Gagal membuat pembayaran*\n\n"
            "Terjadi kesalahan saat menghubungi payment gateway. "
            "Silakan coba lagi nanti.",
            parse_mode="Markdown",
            reply_markup=create_back_keyboard()
        )
        return
    
    # Parse expired_at
    try:
        expired_at = datetime.fromisoformat(payment.expired_at.replace("Z", "+00:00"))
    except:
        expired_at = None
    
    # Save deposit to database
    deposit = create_deposit(
        bot_id=bot_id,
        telegram_id=user.id,
        order_id=order_id,
        amount=amount,
        fee=payment.fee,
        total=payment.total_payment,
        qris_string=payment.payment_number,
        expired_at=expired_at
    )
    
    # Generate QR code
    qr_image = generate_qr_image(payment.payment_number)
    
    # Format amounts
    amount_str = f"Rp {amount:,}".replace(",", ".")
    fee_str = f"Rp {payment.fee:,}".replace(",", ".")
    total_str = f"Rp {payment.total_payment:,}".replace(",", ".")
    
    # Create payment message
    payment_text = (
        f"💳 *Deposit Saldo via QRIS*\n\n"
        f"🆔 *Order:* `{order_id}`\n"
        f"💵 *Deposit:* {amount_str}\n"
        f"📋 *Biaya Admin:* {fee_str}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 *Total Bayar:* {total_str}\n\n"
        f"📱 *Scan QR dengan e-wallet atau mobile banking*\n\n"
        f"⏰ *Berlaku hingga:* {expired_at.strftime('%H:%M WIB') if expired_at else 'N/A'}\n\n"
        f"_Saldo akan otomatis masuk setelah pembayaran berhasil._"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Cek Status", callback_data=f"dep_check_{order_id}")],
        [InlineKeyboardButton("❌ Batalkan", callback_data=f"dep_cancel_{order_id}")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_menu")]
    ])
    
    # Delete previous message
    await query.delete_message()
    
    # Send QR code
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=qr_image,
        caption=payment_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def check_deposit_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check deposit payment status."""
    query = update.callback_query
    await query.answer("🔄 Memeriksa status...")
    
    bot_id = context.bot_data.get('bot_id')
    pakasir_slug = context.bot_data.get('pakasir_slug')
    pakasir_api_key = context.bot_data.get('pakasir_api_key')
    user = update.effective_user
    
    # Extract order ID
    order_id = query.data.replace("dep_check_", "")
    
    deposit = get_deposit_by_order_id(order_id)
    
    if not deposit:
        await query.message.reply_text("❌ Deposit tidak ditemukan.")
        return
    
    if deposit['status'] == "paid":
        balance = get_user_balance(bot_id, user.id)
        balance_str = f"Rp {balance:,}".replace(",", ".")
        await query.message.reply_text(
            f"✅ *Deposit Sudah Berhasil!*\n\n"
            f"Order `{order_id}` sudah terbayar.\n"
            f"💰 *Saldo Anda:* {balance_str}",
            parse_mode="Markdown"
        )
        return
    
    # Check from Pakasir
    pakasir = PakasirClient(pakasir_slug, pakasir_api_key)
    status = await pakasir.get_transaction_status(order_id, deposit['amount'])
    
    if status and status.status == "completed":
        # Update deposit status
        update_deposit_status(order_id, "paid", datetime.now())
        
        # Add balance to user
        add_user_balance(bot_id, user.id, deposit['amount'])
        
        balance = get_user_balance(bot_id, user.id)
        balance_str = f"Rp {balance:,}".replace(",", ".")
        amount_str = f"Rp {deposit['amount']:,}".replace(",", ".")
        
        await query.message.reply_text(
            f"✅ *Deposit Berhasil!*\n\n"
            f"💵 *Deposit:* +{amount_str}\n"
            f"💰 *Saldo Anda:* {balance_str}\n\n"
            f"Terima kasih! Saldo sudah bisa digunakan untuk berbelanja.",
            parse_mode="Markdown",
            reply_markup=create_back_keyboard()
        )
    else:
        await query.message.reply_text(
            f"⏳ *Deposit Belum Diterima*\n\n"
            f"Order `{order_id}` masih menunggu pembayaran.\n"
            f"Silakan scan QRIS dan selesaikan pembayaran.",
            parse_mode="Markdown"
        )


async def cancel_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel pending deposit."""
    query = update.callback_query
    await query.answer()
    
    pakasir_slug = context.bot_data.get('pakasir_slug')
    pakasir_api_key = context.bot_data.get('pakasir_api_key')
    
    # Extract order ID
    order_id = query.data.replace("dep_cancel_", "")
    
    deposit = get_deposit_by_order_id(order_id)
    
    if not deposit:
        await query.message.reply_text("❌ Deposit tidak ditemukan.")
        return
    
    if deposit['status'] != "pending":
        await query.message.reply_text(
            f"⚠️ Deposit `{order_id}` tidak dapat dibatalkan (status: {deposit['status']})",
            parse_mode="Markdown"
        )
        return
    
    # Cancel on Pakasir
    pakasir = PakasirClient(pakasir_slug, pakasir_api_key)
    await pakasir.cancel_transaction(order_id, deposit['amount'])
    
    # Update local status
    update_deposit_status(order_id, "cancelled")
    
    await query.message.reply_text(
        f"✅ *Deposit Dibatalkan*\n\n"
        f"Order `{order_id}` telah dibatalkan.",
        parse_mode="Markdown",
        reply_markup=create_back_keyboard()
    )
