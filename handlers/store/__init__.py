"""
Store Bot Handlers Package.
Handlers for digital product store bot type.
ChenStore-style UI with stats, deposit, and leaderboard.
"""

from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)

from .start import (
    start_command, back_to_menu, help_menu,
    show_leaderboard, show_balance, show_all_products
)
from .catalog import show_catalog, show_category_products, show_product_detail
from .order import (
    show_buy_confirmation,
    process_purchase,
    check_payment_status,
    cancel_payment,
    show_my_orders
)
from .deposit import (
    show_deposit_menu,
    process_deposit,
    check_deposit_status,
    cancel_deposit
)
from .admin import (
    admin_menu,
    admin_categories,
    admin_category_detail,
    admin_category_toggle,
    admin_category_delete,
    admin_category_add_start,
    admin_category_add_name,
    admin_category_add_desc,
    admin_products,
    admin_product_detail,
    admin_product_toggle,
    admin_product_delete,
    admin_product_add_start,
    admin_product_select_category,
    admin_product_add_name,
    admin_product_add_desc,
    admin_product_add_price,
    admin_product_add_content,
    admin_cancel,
    admin_orders,
    admin_stats,
    CAT_NAME, CAT_DESC,
    PROD_NAME, PROD_DESC, PROD_PRICE, PROD_CONTENT, PROD_CATEGORY
)


def get_all_store_handlers(bot_id: int) -> list:
    """
    Get all handlers for a store bot.
    
    Args:
        bot_id: Database ID of the bot
        
    Returns:
        List of handlers to register
    """
    handlers = []
    
    # === ADMIN HANDLERS (must be first for ConversationHandler priority) ===
    
    # Add Category Conversation
    add_category_conv = ConversationHandler(
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
        per_message=False
    )
    handlers.append(add_category_conv)
    
    # Add Product Conversation
    add_product_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_product_add_start, pattern="^admin_prod_add$")
        ],
        states={
            PROD_CATEGORY: [CallbackQueryHandler(admin_product_select_category, pattern="^addprod_cat_\\d+$")],
            PROD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product_add_name)],
            PROD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product_add_desc)],
            PROD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product_add_price)],
            PROD_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product_add_content)],
        },
        fallbacks=[
            CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$")
        ],
        per_message=False
    )
    handlers.append(add_product_conv)
    
    # Admin menu and callbacks
    handlers.extend([
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
    ])
    
    # === START / MENU HANDLERS ===
    handlers.extend([
        CommandHandler("start", start_command),
        CallbackQueryHandler(back_to_menu, pattern="^back_menu$"),
        CallbackQueryHandler(help_menu, pattern="^menu_help$"),
        CallbackQueryHandler(show_leaderboard, pattern="^menu_leaderboard$"),
        CallbackQueryHandler(show_balance, pattern="^menu_balance$"),
        CallbackQueryHandler(show_all_products, pattern="^menu_all_products$"),
    ])
    
    # === CATALOG HANDLERS ===
    handlers.extend([
        CallbackQueryHandler(show_catalog, pattern="^menu_catalog$"),
        CallbackQueryHandler(show_category_products, pattern="^cat_\\d+$"),
        CallbackQueryHandler(show_product_detail, pattern="^prod_\\d+$"),
    ])
    
    # === ORDER HANDLERS ===
    handlers.extend([
        CallbackQueryHandler(show_buy_confirmation, pattern="^buy_\\d+$"),
        CallbackQueryHandler(process_purchase, pattern="^confirm_buy_\\d+$"),
        CallbackQueryHandler(check_payment_status, pattern="^check_[A-Z0-9]+$"),
        CallbackQueryHandler(cancel_payment, pattern="^cancel_[A-Z0-9]+$"),
        CallbackQueryHandler(show_my_orders, pattern="^menu_orders$"),
    ])
    
    # === DEPOSIT HANDLERS ===
    handlers.extend([
        CallbackQueryHandler(show_deposit_menu, pattern="^menu_deposit$"),
        CallbackQueryHandler(process_deposit, pattern="^deposit_\\d+$"),
        CallbackQueryHandler(check_deposit_status, pattern="^dep_check_[A-Z0-9]+$"),
        CallbackQueryHandler(cancel_deposit, pattern="^dep_cancel_[A-Z0-9]+$"),
    ])
    
    return handlers
