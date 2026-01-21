"""
SheerID Verification Handlers for Telegram Bot.
Handles verification commands and callbacks.
"""

import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database_pg import (
    get_pv_user,
    get_or_create_pv_user,
    deduct_pv_balance,
    add_pv_verification,
    get_pv_user_verifications
)
from services.sheerid import VERIFY_TYPES, SheerIDVerifier

logger = logging.getLogger(__name__)

# Conversation states
WAITING_URL = 1


def create_verify_types_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for verification type selection."""
    keyboard = []
    row = []
    
    for type_id, config in VERIFY_TYPES.items():
        btn = InlineKeyboardButton(
            f"{config['icon']} {config['name']} ({config['cost']}pts)",
            callback_data=f"sheerid_type_{type_id}"
        )
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="sheerid_cancel")])
    return InlineKeyboardMarkup(keyboard)


def create_sheerid_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main SheerID menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔐 Verifikasi Baru", callback_data="sheerid_new")],
        [InlineKeyboardButton("📋 Riwayat Verifikasi", callback_data="sheerid_history")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def sheerid_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /verify command - show SheerID menu."""
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    
    # Get or create user
    pv_user = get_or_create_pv_user(
        bot_id=bot_id,
        telegram_id=user.id,
        username=user.username,
        full_name=user.first_name
    )
    
    balance = pv_user.get('balance', 0)
    
    text = (
        f"🔐 *SheerID Verification*\n\n"
        f"Verifikasi akun student/teacher untuk layanan premium seperti:\n"
        f"• YouTube Premium Student\n"
        f"• Spotify Premium Student\n"
        f"• Apple TV+ Student\n"
        f"• Dan lainnya...\n\n"
        f"💰 *Saldo kamu:* {balance} poin\n\n"
        f"Pilih menu di bawah:"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=create_sheerid_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=create_sheerid_menu_keyboard()
        )


async def sheerid_new_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start new verification - show type selection."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    pv_user = get_pv_user(bot_id, user.id)
    balance = pv_user.get('balance', 0) if pv_user else 0
    
    text = (
        f"🔐 *Pilih Tipe Verifikasi*\n\n"
        f"💰 Saldo kamu: {balance} poin\n\n"
        f"Pilih layanan yang ingin diverifikasi:"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_verify_types_keyboard()
    )


async def sheerid_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verification type selection."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    
    # Extract type from callback data
    type_id = query.data.replace("sheerid_type_", "")
    type_config = VERIFY_TYPES.get(type_id)
    
    if not type_config:
        await query.edit_message_text("❌ Tipe verifikasi tidak valid.")
        return ConversationHandler.END
    
    # Check balance
    pv_user = get_pv_user(bot_id, user.id)
    balance = pv_user.get('balance', 0) if pv_user else 0
    cost = type_config['cost']
    
    if balance < cost:
        await query.edit_message_text(
            f"❌ *Saldo Tidak Cukup*\n\n"
            f"Biaya: {cost} poin\n"
            f"Saldo kamu: {balance} poin\n\n"
            f"Dapatkan poin dengan daily check-in atau undang teman!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_sheerid")]
            ])
        )
        return ConversationHandler.END
    
    # Store selected type in user_data
    context.user_data['sheerid_type'] = type_id
    context.user_data['sheerid_cost'] = cost
    
    text = (
        f"🔐 *{type_config['name']}*\n\n"
        f"💰 Biaya: {cost} poin\n\n"
        f"📋 *Instruksi:*\n"
        f"1. Buka layanan ({type_config['name']})\n"
        f"2. Mulai verifikasi student\n"
        f"3. Copy URL dari halaman SheerID\n"
        f"4. Kirim URL ke sini\n\n"
        f"Kirim URL SheerID sekarang (harus mengandung `verificationId`):"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Batal", callback_data="sheerid_cancel")]
        ])
    )
    
    return WAITING_URL


async def sheerid_receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle URL input from user."""
    import time
    from datetime import datetime
    
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    url = update.message.text.strip()
    
    verify_type = context.user_data.get('sheerid_type')
    cost = context.user_data.get('sheerid_cost', 5)
    
    # Validate URL
    if "sheerid.com" not in url.lower():
        await update.message.reply_text(
            "❌ URL tidak valid. Harus berisi URL dari SheerID.\n"
            "Contoh: `https://services.sheerid.com/verify/...?verificationId=...`",
            parse_mode="Markdown"
        )
        return WAITING_URL
    
    # Extract verification ID
    vid_match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
    if not vid_match:
        vid_match = re.search(r"/verification/([a-f0-9]+)", url, re.IGNORECASE)
    
    if not vid_match:
        await update.message.reply_text(
            "❌ URL tidak valid. Tidak menemukan `verificationId`.\n"
            "Pastikan URL mengandung parameter `verificationId`.",
            parse_mode="Markdown"
        )
        return WAITING_URL
    
    verify_id = vid_match.group(1)
    
    # Deduct balance first
    if not deduct_pv_balance(bot_id, user.id, cost):
        await update.message.reply_text(
            f"❌ Gagal memotong saldo. Pastikan saldo kamu cukup ({cost} poin)."
        )
        return ConversationHandler.END
    
    # Record start time
    start_time = time.time()
    submit_time = datetime.now()
    submit_time_str = submit_time.strftime("%H:%M:%S %d/%m/%Y")
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"⏳ *Memproses Verifikasi...*\n\n"
        f"Tipe: {VERIFY_TYPES[verify_type]['name']}\n"
        f"ID: `{verify_id[:8]}...`\n"
        f"🕐 Mulai: {submit_time_str}\n\n"
        f"Mohon tunggu, proses ini bisa memakan waktu 30-60 detik...",
        parse_mode="Markdown"
    )
    
    try:
        # Get owner's proxy from dashboard settings
        from database_pg import get_owner_proxy, OWNER_TELEGRAM_ID
        import os
        import httpx
        
        owner_user_id = os.getenv("OWNER_USER_ID", "Not Set")
        proxy = get_owner_proxy()
        
        # Detailed proxy logging with IP geolocation
        proxy_location = ""
        proxy_ip = ""
        
        if proxy:
            # Mask password in proxy URL for display
            proxy_display = proxy
            if "@" in proxy:
                parts = proxy.split("@")
                auth_parts = parts[0].replace("http://", "").split(":")
                if len(auth_parts) >= 2:
                    proxy_display = f"http://{auth_parts[0]}:****@{parts[1]}"
            
            # Try to get proxy IP and location
            try:
                client = httpx.Client(proxy=proxy, timeout=10)
                resp = client.get("https://ipapi.co/json/")
                if resp.status_code == 200:
                    ip_data = resp.json()
                    proxy_ip = ip_data.get("ip", "Unknown")
                    city = ip_data.get("city", "")
                    country = ip_data.get("country_name", "")
                    country_code = ip_data.get("country_code", "")
                    
                    if city and country:
                        proxy_location = f"📍 {city}, {country} ({country_code})"
                    elif country:
                        proxy_location = f"📍 {country} ({country_code})"
                    
                    logger.info(f"[VERIFY] Proxy IP: {proxy_ip} - Location: {city}, {country}")
                client.close()
            except Exception as e:
                logger.warning(f"[VERIFY] Could not get proxy IP info: {e}")
                proxy_location = "📍 Location unknown"
            
            proxy_status = f"✅ Proxy Aktif"
            if proxy_location:
                proxy_status += f"\n{proxy_location}"
            if proxy_ip:
                proxy_status += f"\n🔗 IP: {proxy_ip}"
            
            logger.info(f"[VERIFY] User {user.id} - Using proxy: {proxy_display}")
            logger.info(f"[VERIFY] OWNER_USER_ID={owner_user_id}, OWNER_TELEGRAM_ID={OWNER_TELEGRAM_ID}")
        else:
            proxy_status = "⚠️ Tanpa Proxy (Direct Connection)"
            logger.warning(f"[VERIFY] User {user.id} - NO PROXY CONFIGURED!")
            logger.warning(f"[VERIFY] OWNER_USER_ID={owner_user_id} - Check if proxy is activated in dashboard")
        
        # Update processing message with proxy info
        await processing_msg.edit_text(
            f"⏳ *Memproses Verifikasi...*\n\n"
            f"Tipe: {VERIFY_TYPES[verify_type]['name']}\n"
            f"ID: `{verify_id[:8]}...`\n"
            f"🕐 Mulai: {submit_time_str}\n\n"
            f"{proxy_status}\n\n"
            f"Mohon tunggu...",
            parse_mode="Markdown"
        )
        
        # Run verification with proxy
        logger.info(f"[VERIFY] Starting verification for {verify_type} - ID: {verify_id[:8]}...")
        verifier = SheerIDVerifier(url, verify_type, proxy=proxy)
        result = verifier.verify()
        
        # Calculate duration
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        duration_str = f"{duration}s"
        
        logger.info(f"[VERIFY] Completed in {duration_str} - Success: {result.get('success')} - Final Step: {result.get('final_step')}")
        
        if result.get('success'):
            student_name = result.get('student_name', 'N/A')
            final_step = result.get('final_step', 'pending')
            
            # Check actual status from SheerID
            if final_step == 'success':
                # Actually approved!
                await processing_msg.edit_text(
                    f"✅ *Verifikasi Berhasil!*\n\n"
                    f"Tipe: {VERIFY_TYPES[verify_type]['name']}\n"
                    f"Nama: {student_name}\n"
                    f"Biaya: {cost} poin\n\n"
                    f"📊 *Info Proses:*\n"
                    f"🕐 Submit: {submit_time_str}\n"
                    f"⏱️ Durasi: {duration_str}\n"
                    f"{proxy_status}\n\n"
                    f"🎉 Silakan kembali ke layanan untuk klaim benefit!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Menu SheerID", callback_data="menu_sheerid")]
                    ])
                )
                
                # Record as success
                add_pv_verification(
                    bot_id, user.id, verify_type, url, 
                    "success", result.get('message', 'Approved'), verify_id
                )
            else:
                # Pending review - NOT approved yet
                await processing_msg.edit_text(
                    f"⏳ *Verifikasi Dalam Review*\n\n"
                    f"Tipe: {VERIFY_TYPES[verify_type]['name']}\n"
                    f"Nama: {student_name}\n"
                    f"Biaya: {cost} poin\n\n"
                    f"📋 Status: *PENDING* (Dalam Review)\n"
                    f"⏰ Estimasi: 24-48 jam\n\n"
                    f"📊 *Info Proses:*\n"
                    f"🕐 Submit: {submit_time_str}\n"
                    f"⏱️ Durasi: {duration_str}\n"
                    f"{proxy_status}\n\n"
                    f"Dokumen berhasil disubmit, menunggu verifikasi manual.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Menu SheerID", callback_data="menu_sheerid")]
                    ])
                )
                
                # Record as pending
                add_pv_verification(
                    bot_id, user.id, verify_type, url,
                    "pending", result.get('message', 'Awaiting review'), verify_id
                )
        else:
            # Failed - refund
            from database_pg import add_pv_balance
            add_pv_balance(bot_id, user.id, cost)
            
            error = result.get('error', 'Unknown error')
            logger.error(f"[VERIFY] FAILED - Error: {error} - Duration: {duration_str}")
            
            await processing_msg.edit_text(
                f"❌ *Verifikasi Gagal*\n\n"
                f"Error: {error}\n\n"
                f"📊 *Info Proses:*\n"
                f"🕐 Submit: {submit_time_str}\n"
                f"⏱️ Durasi: {duration_str}\n"
                f"{proxy_status}\n\n"
                f"💰 Saldo {cost} poin dikembalikan.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Coba Lagi", callback_data="sheerid_new")],
                    [InlineKeyboardButton("🔙 Menu SheerID", callback_data="menu_sheerid")]
                ])
            )
            
            # Record failure
            add_pv_verification(
                bot_id, user.id, verify_type, url,
                "failed", error, verify_id
            )
    
    except Exception as e:
        logger.error(f"SheerID verification error: {e}")
        
        # Refund on error
        from database_pg import add_pv_balance
        add_pv_balance(bot_id, user.id, cost)
        
        await processing_msg.edit_text(
            f"❌ *Terjadi Kesalahan*\n\n"
            f"Error: {str(e)}\n\n"
            f"💰 Saldo {cost} poin dikembalikan.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Menu SheerID", callback_data="menu_sheerid")]
            ])
        )
    
    # Clear user data
    context.user_data.pop('sheerid_type', None)
    context.user_data.pop('sheerid_cost', None)
    
    return ConversationHandler.END


async def sheerid_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show verification history."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    
    verifications = get_pv_user_verifications(bot_id, user.id)
    
    if not verifications:
        await query.edit_message_text(
            "📋 *Riwayat Verifikasi*\n\n"
            "Belum ada riwayat verifikasi.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kembali", callback_data="menu_sheerid")]
            ])
        )
        return
    
    text = "📋 *Riwayat Verifikasi*\n\n"
    
    for v in verifications[:10]:  # Show last 10
        status_icon = "✅" if v.get('status') == 'success' else "❌"
        type_name = VERIFY_TYPES.get(v.get('verify_type', ''), {}).get('name', v.get('verify_type', 'Unknown'))
        date = v.get('created_at', 'N/A')
        if hasattr(date, 'strftime'):
            date = date.strftime('%d/%m/%Y %H:%M')
        
        text += f"{status_icon} *{type_name}*\n"
        text += f"   📅 {date}\n\n"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Kembali", callback_data="menu_sheerid")]
        ])
    )


async def sheerid_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel verification process."""
    query = update.callback_query
    await query.answer("Dibatalkan")
    
    # Clear user data
    context.user_data.pop('sheerid_type', None)
    context.user_data.pop('sheerid_cost', None)
    
    await sheerid_menu(update, context)
    return ConversationHandler.END


def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard for SheerID bot."""
    keyboard = [
        [InlineKeyboardButton("🔐 SheerID Verification", callback_data="menu_sheerid")],
        [
            InlineKeyboardButton("💰 Saldo", callback_data="sheerid_balance"),
            InlineKeyboardButton("📅 Daily Check-in", callback_data="sheerid_checkin"),
        ],
        [InlineKeyboardButton("🔗 Referral", callback_data="sheerid_referral")],
        [InlineKeyboardButton("ℹ️ Bantuan", callback_data="sheerid_help")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - show main menu."""
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    
    # Check for referral
    invited_by = None
    if context.args and context.args[0].startswith('ref'):
        try:
            invited_by = int(context.args[0].replace('ref', ''))
            if invited_by == user.id:
                invited_by = None  # Can't invite yourself
        except:
            pass
    
    # Get or create user
    pv_user = get_or_create_pv_user(
        bot_id=bot_id,
        telegram_id=user.id,
        username=user.username,
        full_name=user.first_name,
        invited_by=invited_by
    )
    
    balance = pv_user.get('balance', 0)
    
    text = (
        f"👋 *Selamat datang, {user.first_name}!*\n\n"
        f"🔐 *SheerID Verification Bot*\n"
        f"Verifikasi akun student/teacher otomatis untuk layanan premium.\n\n"
        f"💰 Saldo: *{balance} poin*\n\n"
        f"Pilih menu di bawah:"
    )
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_main_menu_keyboard()
    )


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to main menu."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    pv_user = get_pv_user(bot_id, user.id)
    balance = pv_user.get('balance', 0) if pv_user else 0
    
    text = (
        f"👋 *Menu Utama*\n\n"
        f"🔐 *SheerID Verification Bot*\n\n"
        f"💰 Saldo: *{balance} poin*\n\n"
        f"Pilih menu di bawah:"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=create_main_menu_keyboard()
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user balance."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    pv_user = get_pv_user(bot_id, user.id)
    balance = pv_user.get('balance', 0) if pv_user else 0
    
    text = (
        f"💰 *Saldo Kamu*\n\n"
        f"Balance: *{balance} poin*\n\n"
        f"*Cara Dapat Poin:*\n"
        f"• 📅 Daily Check-in: +1 poin/hari\n"
        f"• 🔗 Undang Teman: +2 poin/orang\n"
        f"• 🎁 Kode Voucher: Jumlah bervariasi"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Daily Check-in", callback_data="sheerid_checkin")],
            [InlineKeyboardButton("🔗 Referral", callback_data="sheerid_referral")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]
        ])
    )


async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle daily check-in."""
    from database_pg import pv_checkin, can_pv_checkin
    
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    bot_id = context.bot_data.get('bot_id')
    
    if can_pv_checkin(bot_id, user.id):
        if pv_checkin(bot_id, user.id):
            pv_user = get_pv_user(bot_id, user.id)
            new_balance = pv_user.get('balance', 0)
            text = (
                f"✅ *Check-in Berhasil!*\n\n"
                f"+1 poin ditambahkan\n"
                f"Saldo sekarang: *{new_balance} poin*\n\n"
                f"Jangan lupa check-in lagi besok!"
            )
        else:
            text = "❌ Terjadi kesalahan saat check-in."
    else:
        text = (
            "⏰ *Sudah Check-in Hari Ini*\n\n"
            "Kamu sudah check-in hari ini.\n"
            "Coba lagi besok!"
        )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]
        ])
    )


async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral link."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    bot_username = (await context.bot.get_me()).username
    
    ref_link = f"https://t.me/{bot_username}?start=ref{user.id}"
    
    text = (
        f"🔗 *Referral Program*\n\n"
        f"Link referral kamu:\n"
        f"`{ref_link}`\n\n"
        f"*Bonus:*\n"
        f"• Kamu dapat +2 poin setiap teman join\n"
        f"• Teman dapat +1 poin saat register\n\n"
        f"Share link di atas ke teman-temanmu!"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]
        ])
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help."""
    query = update.callback_query
    await query.answer()
    
    text = (
        "ℹ️ *Bantuan*\n\n"
        "*Cara Verifikasi SheerID:*\n"
        "1. Buka layanan (YouTube, Spotify, dll)\n"
        "2. Mulai proses verifikasi student\n"
        "3. Copy URL dari halaman SheerID\n"
        "4. Paste ke bot ini\n"
        "5. Tunggu hasilnya!\n\n"
        "*Layanan yang Didukung:*\n"
        "• YouTube Premium\n"
        "• Spotify Premium\n"
        "• Apple TV+\n"
        "• HBO Max\n"
        "• Dan lainnya\n\n"
        "*Pertanyaan?*\n"
        "Hubungi admin untuk bantuan."
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]
        ])
    )


def get_sheerid_handlers(bot_id: int) -> list:
    """
    Get all SheerID handlers.
    
    Args:
        bot_id: Database ID of the bot
        
    Returns:
        List of handlers to register
    """
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
    
    handlers = []
    
    # Verification conversation handler (must be first for priority)
    verify_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(sheerid_type_selected, pattern="^sheerid_type_"),
        ],
        states={
            WAITING_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sheerid_receive_url),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(sheerid_cancel, pattern="^sheerid_cancel$"),
            CommandHandler("start", start_command),
        ],
        per_message=False
    )
    handlers.append(verify_conv)
    
    # Main commands
    handlers.extend([
        CommandHandler("start", start_command),
        CommandHandler("verify", sheerid_menu),
    ])
    
    # Menu callbacks
    handlers.extend([
        CallbackQueryHandler(back_to_menu, pattern="^back_menu$"),
        CallbackQueryHandler(sheerid_menu, pattern="^menu_sheerid$"),
        CallbackQueryHandler(sheerid_new_verification, pattern="^sheerid_new$"),
        CallbackQueryHandler(sheerid_type_selected, pattern="^sheerid_type_"),
        CallbackQueryHandler(sheerid_history, pattern="^sheerid_history$"),
        CallbackQueryHandler(sheerid_cancel, pattern="^sheerid_cancel$"),
        CallbackQueryHandler(balance_command, pattern="^sheerid_balance$"),
        CallbackQueryHandler(checkin_command, pattern="^sheerid_checkin$"),
        CallbackQueryHandler(referral_command, pattern="^sheerid_referral$"),
        CallbackQueryHandler(help_command, pattern="^sheerid_help$"),
    ])
    
    return handlers

