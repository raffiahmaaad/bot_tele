"""
Database migration script to add deposit system tables.
Run this once to update the database schema.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

def run_migration():
    """Run database migration for deposit system."""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        print("Running database migrations...")
        
        # Add balance column to bot_users
        print("  - Adding balance column to bot_users...")
        cursor.execute("""
            ALTER TABLE bot_users ADD COLUMN IF NOT EXISTS balance INTEGER DEFAULT 0
        """)
        
        # Create deposits table
        print("  - Creating deposits table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                telegram_id BIGINT NOT NULL,
                order_id VARCHAR(50) UNIQUE NOT NULL,
                amount INTEGER NOT NULL,
                fee INTEGER DEFAULT 0,
                total INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                qris_string TEXT,
                expired_at TIMESTAMP,
                paid_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create index on deposits
        print("  - Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_deposits_bot_id ON deposits(bot_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_deposits_telegram_id ON deposits(telegram_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_deposits_status ON deposits(status)
        """)
        
        conn.commit()
        print("✅ Database migrations completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
