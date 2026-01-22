"""
Store Bot - Start Handler.
Handles /start command and main menu for store bots.
ChenStore-style UI with stats and category buttons.
"""

import os
from telegram import Update
from telegram.ext import ContextTypes

from database_pg import (
    get_or_create_bot_user, 
    get_store_stats, 
    get_categories_by_bot,
    get_user_balance,
    get_leaderboard,
    get_products_by_bot
)
from utils.keyboard import create_menu_keyboard, create_admin_menu_keyboard, create_back_keyboard

# Owner Telegram ID for admin access
OWNER_TELEGRAM_ID = int(os.getenv("OWNER_TELEGRAM_ID", "0"))


def is_owner(user_id: int) -> bool:
    """Check if user is the owner (admin of all bots)."""
    return user_id == OWNER_TELEGRAM_ID


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - show main menu with stats (ChenStore style)."""
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    bot_name = context.bot_data.get('bot_name', 'Digital Store')
    
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
    
    # Get store stats for display
    stats = get_store_stats(bot_id)
    categories = get_categories_by_bot(bot_id)
    balance = get_user_balance(bot_id, user.id)
    
    # Build ChenStore-style welcome message
    welcome_text = (
        f"— Hai, {user.first_name} 👋\n\n"
        f"Selamat datang di *{bot_name}*\n"
        f"• Total User Bot: 👤 {stats['total_users']} Orang\n"
        f"• Total Transaksi Terselesaikan: {stats['total_transactions']}x\n\n"
        f"Tekan Button dibawah untuk melihat list produk yang dijual di list "
        f"untuk melihat produk apa saja yang dijual di store ini 🔥"
    )
    
    # Use admin keyboard if user is owner
    if is_admin:
        keyboard = create_admin_menu_keyboard(categories, balance)
    else:
        keyboard = create_menu_keyboard(categories, balance)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to menu callback - return to main menu with stats."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    bot_name = context.bot_data.get('bot_name', 'Digital Store')
    is_admin = is_owner(user.id)
    
    # Get store stats for display
    stats = get_store_stats(bot_id)
    categories = get_categories_by_bot(bot_id)
    balance = get_user_balance(bot_id, user.id)
    
    # Build ChenStore-style welcome message
    welcome_text = (
        f"— Hai, {user.first_name} 👋\n\n"
        f"Selamat datang di *{bot_name}*\n"
        f"• Total User Bot: 👤 {stats['total_users']} Orang\n"
        f"• Total Transaksi Terselesaikan: {stats['total_transactions']}x\n\n"
        f"Tekan Button dibawah untuk melihat list produk 🔥"
    )
    
    if is_admin:
        keyboard = create_admin_menu_keyboard(categories, balance)
    else:
        keyboard = create_menu_keyboard(categories, balance)
    
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
        "1. Pilih kategori produk dari menu\n"
        "2. Pilih produk dan klik *Beli Sekarang*\n"
        "3. Bayar dengan saldo atau scan QRIS\n"
        "4. Produk dikirim otomatis setelah pembayaran\n\n"
        "*Deposit Saldo:*\n"
        "1. Klik tombol *➕ Deposit*\n"
        "2. Pilih nominal deposit\n"
        "3. Scan QRIS dan bayar\n"
        "4. Saldo otomatis masuk ke akun Anda\n\n"
        "*Metode Pembayaran:*\n"
        "• Saldo Akun - Lebih cepat dan praktis\n"
        "• QRIS - Semua e-wallet & mobile banking\n\n"
        "*Pertanyaan?*\n"
        "Hubungi admin untuk bantuan lebih lanjut."
    )
    
    await query.edit_message_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=create_back_keyboard()
    )


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top buyers leaderboard."""
    query = update.callback_query
    await query.answer()
    
    bot_id = context.bot_data.get('bot_id')
    leaderboard = get_leaderboard(bot_id, limit=10)
    
    if not leaderboard:
        text = (
            "🏆 *Leaderboard*\n\n"
            "📭 Belum ada transaksi. Jadilah yang pertama berbelanja!"
        )
    else:
        text = "🏆 *Leaderboard - Top Buyers*\n\n"
        medals = ["🥇", "🥈", "🥉"]
        
        for i, buyer in enumerate(leaderboard):
            medal = medals[i] if i < 3 else f"{i+1}."
            name = buyer.get('first_name') or buyer.get('username') or 'Anonymous'
            total_str = f"Rp {buyer['total_spent']:,}".replace(",", ".")
            text += f"{medal} *{name}*\n"
            text += f"    💰 {total_str} ({buyer['total_orders']} transaksi)\n\n"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_back_keyboard()
    )


async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user balance details."""
    query = update.callback_query
    await query.answer()
    
    bot_id = context.bot_data.get('bot_id')
    user = update.effective_user
    balance = get_user_balance(bot_id, user.id)
    balance_str = f"Rp {balance:,}".replace(",", ".")
    
    text = (
        f"💰 *Saldo Anda*\n\n"
        f"💵 *Balance:* {balance_str}\n\n"
        f"Gunakan saldo untuk berbelanja lebih cepat tanpa perlu scan QRIS setiap kali.\n\n"
        f"_Klik Deposit untuk menambah saldo._"
    )
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Deposit Saldo", callback_data="menu_deposit")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]
    ])
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def show_all_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all products from all categories."""
    query = update.callback_query
    await query.answer()
    
    bot_id = context.bot_data.get('bot_id')
    products = get_products_by_bot(bot_id)
    
    if not products:
        text = "📦 *Semua Produk*\n\n📭 Belum ada produk tersedia."
        await query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=create_back_keyboard()
        )
        return
    
    text = f"📦 *Semua Produk* ({len(products)} item)\n\n"
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = []
    
    for prod in products[:20]:  # Limit to 20
        price_str = f"Rp {prod['price']:,}".replace(",", ".")
        stock = prod.get('stock', 0)
        stock_str = f"({stock})" if stock > 0 else "(Habis)"
        keyboard.append([
            InlineKeyboardButton(
                f"{prod['name']} - {price_str} {stock_str}",
                callback_data=f"prod_{prod['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")])
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
