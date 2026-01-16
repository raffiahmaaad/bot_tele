"""
Handler for /start command and main menu.
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from config import config
from database import get_or_create_user
from utils.keyboard import create_menu_keyboard, create_admin_menu_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - show main menu."""
    user = update.effective_user
    
    # Get or create user in database
    db_user = get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name or "User"
    )
    
    # Check if user is admin
    is_admin = user.id in config.ADMIN_TELEGRAM_IDS
    
    # Create welcome message
    welcome_text = (
        f"👋 *Selamat datang, {user.first_name}!*\n\n"
        f"🛒 *Digital Store Bot*\n"
        f"Toko produk digital dengan pembayaran QRIS\n\n"
        f"Pilih menu di bawah untuk memulai:"
    )
    
    # Use admin keyboard if user is admin
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
    is_admin = user.id in config.ADMIN_TELEGRAM_IDS
    
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


def get_start_handlers():
    """Get all handlers for start module."""
    return [
        CommandHandler("start", start_command),
        CallbackQueryHandler(back_to_menu, pattern="^back_menu$"),
        CallbackQueryHandler(help_menu, pattern="^menu_help$"),
    ]
