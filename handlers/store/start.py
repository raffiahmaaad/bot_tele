"""
Store Bot - Start Handler.
Handles /start command and main menu for store bots.
"""

import os
from telegram import Update
from telegram.ext import ContextTypes

from database_pg import get_or_create_bot_user
from utils.keyboard import create_menu_keyboard, create_admin_menu_keyboard

# Owner Telegram ID for admin access
OWNER_TELEGRAM_ID = int(os.getenv("OWNER_TELEGRAM_ID", "0"))


def is_owner(user_id: int) -> bool:
    """Check if user is the owner (admin of all bots)."""
    return user_id == OWNER_TELEGRAM_ID


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - show main menu."""
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    
    # Get or create bot user in database
    bot_user = get_or_create_bot_user(
        bot_id=bot_id,
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name or "User"
    )
    
    # Store bot_user_id in user_data for later use
    context.user_data['bot_user_id'] = bot_user['id']
    
    # Check if user is owner (admin)
    is_admin = is_owner(user.id)
    
    # Check for custom command response from dashboard
    from database_pg import get_bot_command
    custom_cmd = get_bot_command(bot_id, 'start')
    
    if custom_cmd and custom_cmd.get('response_text'):
        # Use custom response from dashboard
        welcome_text = custom_cmd['response_text']
    else:
        # Default welcome message
        welcome_text = (
            f"👋 *Selamat datang, {user.first_name}!*\n\n"
            f"🛒 *Digital Store Bot*\n"
            f"Toko produk digital dengan pembayaran QRIS\n\n"
            f"Pilih menu di bawah untuk memulai:"
        )
    
    # Use admin keyboard if user is owner
    keyboard = create_admin_menu_keyboard() if is_admin else create_menu_keyboard()
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to menu callback."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    is_admin = is_owner(user.id)
    
    # Check for custom command response from dashboard
    from database_pg import get_bot_command
    custom_cmd = get_bot_command(bot_id, 'menu') if bot_id else None
    
    if custom_cmd and custom_cmd.get('response_text'):
        welcome_text = custom_cmd['response_text']
    else:
        welcome_text = (
            f"👋 *Selamat datang, {user.first_name}!*\n\n"
            f"🛒 *Digital Store Bot*\n"
            f"Toko produk digital dengan pembayaran QRIS\n\n"
            f"Pilih menu di bawah untuk memulai:"
        )
    
    keyboard = create_admin_menu_keyboard() if is_admin else create_menu_keyboard()
    
    await query.edit_message_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help menu callback."""
    query = update.callback_query
    await query.answer()
    
    help_text = (
        "ℹ️ *Bantuan*\n\n"
        "*Cara Berbelanja:*\n"
        "1. Pilih *Katalog Produk* dari menu\n"
        "2. Pilih kategori yang diinginkan\n"
        "3. Pilih produk dan klik *Beli Sekarang*\n"
        "4. Scan QRIS yang muncul dengan aplikasi pembayaran\n"
        "5. Setelah pembayaran berhasil, produk akan dikirim otomatis\n\n"
        "*Metode Pembayaran:*\n"
        "• QRIS - Bisa dibayar dengan semua e-wallet & mobile banking\n\n"
        "*Pertanyaan?*\n"
        "Hubungi admin untuk bantuan lebih lanjut."
    )
    
    from utils.keyboard import create_back_keyboard
    
    await query.edit_message_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=create_back_keyboard()
    )
