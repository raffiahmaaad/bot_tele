"""
Test bot startup to check for errors
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("Testing bot imports...")

try:
    from database_pg import get_active_bots
    print("✓ database_pg imported")
except Exception as e:
    print(f"✗ database_pg error: {e}")
    sys.exit(1)

try:
    from bot_manager import BotManager
    print("✓ bot_manager imported")
except Exception as e:
    print(f"✗ bot_manager error: {e}")
    sys.exit(1)

try:
    from handlers.store import get_all_store_handlers
    print("✓ handlers.store imported")
except Exception as e:
    print(f"✗ handlers.store error: {e}")
    sys.exit(1)

print("\nChecking database...")
try:
    bots = get_active_bots()
    print(f"✓ Found {len(bots)} active bot(s)")
    for bot in bots:
        print(f"  - ID: {bot['id']}, Username: @{bot.get('bot_username', 'unknown')}, Type: {bot.get('bot_type', 'store')}")
except Exception as e:
    print(f"✗ Database error: {e}")
    sys.exit(1)

print("\nAll checks passed!")
