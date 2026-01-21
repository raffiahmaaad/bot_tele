"""
Database Schema Update Script

Run this to add new columns and tables to an existing database.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def update_schema():
    """Update database schema with new columns and tables."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False
    
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    try:
        print("🔄 Updating database schema...")
        
        # Add bot_type column if not exists
        print("   Adding bot_type column to bots table...")
        cursor.execute("""
            ALTER TABLE bots 
            ADD COLUMN IF NOT EXISTS bot_type VARCHAR(50) DEFAULT 'store'
        """)
        
        # Create verifications table (for simple verification bot)
        print("   Creating verifications table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verifications (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                telegram_id BIGINT NOT NULL,
                student_id VARCHAR(50),
                full_name VARCHAR(200),
                status VARCHAR(20) DEFAULT 'pending',
                verified_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verifications_bot_telegram 
            ON verifications(bot_id, telegram_id)
        """)
        
        # ==================== POINTS VERIFY TABLES ====================
        print("   Creating points verify tables...")
        
        # PV Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pv_users (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                telegram_id BIGINT NOT NULL,
                username VARCHAR(255),
                full_name VARCHAR(255),
                balance INTEGER DEFAULT 1,
                is_blocked BOOLEAN DEFAULT false,
                invited_by BIGINT,
                last_checkin TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(bot_id, telegram_id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pv_users_bot_telegram 
            ON pv_users(bot_id, telegram_id)
        """)
        
        # PV Invitations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pv_invitations (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                inviter_id BIGINT NOT NULL,
                invitee_id BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # PV Verifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pv_verifications (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                telegram_id BIGINT NOT NULL,
                verify_type VARCHAR(50) NOT NULL,
                verify_url TEXT,
                verify_id VARCHAR(255),
                status VARCHAR(50) NOT NULL,
                result TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pv_verifications_bot_telegram 
            ON pv_verifications(bot_id, telegram_id)
        """)
        
        # PV Card Keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pv_card_keys (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                key_code VARCHAR(100) NOT NULL,
                balance INTEGER NOT NULL,
                max_uses INTEGER DEFAULT 1,
                current_uses INTEGER DEFAULT 0,
                expire_at TIMESTAMP,
                created_by BIGINT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(bot_id, key_code)
            )
        """)
        
        # PV Card Key Usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pv_card_key_usage (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                key_code VARCHAR(100) NOT NULL,
                telegram_id BIGINT NOT NULL,
                used_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # ==================== SHEERID VERIFICATION TABLES ====================
        print("   Creating SheerID verification tables...")
        
        # SheerID Verifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sheerid_verifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                
                verify_type VARCHAR(50) NOT NULL,
                verify_url TEXT NOT NULL,
                verify_id VARCHAR(100),
                
                status VARCHAR(20) DEFAULT 'pending',
                result_message TEXT,
                student_name VARCHAR(100),
                student_email VARCHAR(255),
                school_name VARCHAR(255),
                redirect_url TEXT,
                
                points_cost INTEGER DEFAULT 5,
                points_paid BOOLEAN DEFAULT false,
                
                created_at TIMESTAMP DEFAULT NOW(),
                processed_at TIMESTAMP,
                error_details TEXT
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sheerid_verifications_user 
            ON sheerid_verifications(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sheerid_verifications_status 
            ON sheerid_verifications(status)
        """)
        
        # SheerID Settings table (proxy config)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sheerid_settings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                
                proxy_enabled BOOLEAN DEFAULT false,
                proxy_host VARCHAR(255),
                proxy_port INTEGER,
                proxy_username VARCHAR(255),
                proxy_password VARCHAR(255),
                
                default_points_cost INTEGER DEFAULT 5,
                
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # ==================== USER PROXIES TABLE ====================
        print("   Creating user_proxies table for multi-proxy storage...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_proxies (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(100) NOT NULL,
                host VARCHAR(255) NOT NULL,
                port INTEGER NOT NULL,
                username VARCHAR(255),
                password VARCHAR(255),
                is_active BOOLEAN DEFAULT false,
                last_tested_at TIMESTAMP,
                last_test_success BOOLEAN,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_proxies_user_id 
            ON user_proxies(user_id)
        """)
        
        # ==================== BOT COMMANDS TABLE ====================
        print("   Creating bot_commands table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_commands (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
                command_name VARCHAR(50) NOT NULL,
                response_text TEXT,
                is_enabled BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(bot_id, command_name)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bot_commands_bot_id 
            ON bot_commands(bot_id)
        """)
        
        conn.commit()
        print("✅ Schema updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Schema update failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    update_schema()
