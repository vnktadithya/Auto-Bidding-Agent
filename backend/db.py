import sqlite3
import os
from datetime import datetime

# Resolve path to ensure database stays inside the backend folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bids.db')

# Ensure the backend directory exists (extra safety)
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR, exist_ok=True)

def get_db_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Ensures the database and tables are correctly initialized."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create post_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_url TEXT UNIQUE NOT NULL,
            platform TEXT NOT NULL,
            reply_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Ensure reply_text column exists (migration support)
    try:
        cursor.execute("ALTER TABLE post_history ADD COLUMN reply_text TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    conn.commit()
    conn.close()

def save_post(url, platform, reply_text=None):
    """Saves a post to the history."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO post_history (post_url, platform, reply_text) VALUES (?, ?, ?)", 
            (url, platform, reply_text)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_exists(url):
    """Checks if a URL has already been processed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM post_history WHERE post_url = ?", (url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def get_history(limit=50):
    """Returns the latest post history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT post_url, platform, reply_text, timestamp FROM post_history ORDER BY timestamp DESC LIMIT ?", 
        (limit,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_daily_count(platform):
    """Returns the number of posts for a platform today."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT count(*) FROM post_history WHERE platform = ? AND date(timestamp) = date('now')", 
        (platform,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count
