"""
Check if bot_commands table exists
"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'bot_commands'")
result = cur.fetchone()
print('bot_commands table exists:', result is not None)

if result:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'bot_commands'")
    columns = cur.fetchall()
    print('Columns:', [c[0] for c in columns])

conn.close()
