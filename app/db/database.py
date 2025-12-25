import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "stock_agent.db")

def init_db():
    """Initializes the SQLite database with the required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT,
        black_list TEXT, -- JSON encoded list of strings
        white_list TEXT, -- JSON encoded list of strings (max 30, for prefetch priority)
        return_rate REAL DEFAULT 0.0
    )
    ''')

    # Create index on email for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)')

    # Create stocks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        stock_name TEXT NOT NULL,
        avg_price REAL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # Migration: Add white_list column if it doesn't exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if "white_list" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN white_list TEXT")
        print("✅ Migration: Added white_list column to users table")

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")

def get_db_connection():
    """Helper to get a database connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_users():
    """Fetch all users and parse their black_list and white_list JSON."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    users = []
    for row in rows:
        black_list = []
        white_list = []
        if row["black_list"]:
            try:
                black_list = json.loads(row["black_list"])
            except:
                pass
        if row["white_list"]:
            try:
                white_list = json.loads(row["white_list"])
            except:
                pass

        users.append({
            "id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"] or "",
            "black_list": black_list,
            "white_list": white_list,
            "return_rate": row["return_rate"] or 0.0
        })
    conn.close()
    return users

def update_user_settings(user_id, black_list, return_rate, white_list=None):
    """Update user settings including whitelist and return the updated user object or None."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return None

    # Update - include white_list if provided
    if white_list is not None:
        cursor.execute(
            "UPDATE users SET black_list = ?, white_list = ?, return_rate = ? WHERE id = ?",
            (json.dumps(black_list), json.dumps(white_list), return_rate, user_id)
        )
    else:
        cursor.execute(
            "UPDATE users SET black_list = ?, return_rate = ? WHERE id = ?",
            (json.dumps(black_list), return_rate, user_id)
        )
    conn.commit()

    # Fetch updated
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    return {
        "id": row["id"],
        "email": row["email"],
        "full_name": row["full_name"] or "",
        "black_list": black_list,
        "white_list": json.loads(row["white_list"]) if row["white_list"] else [],
        "return_rate": row["return_rate"] or 0.0
    }

def get_user_stocks(user_id):
    """Fetch all stocks for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stocks WHERE user_id = ?", (user_id,))
    stocks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return stocks

def add_user_stock(user_id, stock_name, avg_price):
    """Add a new stock to a user's portfolio."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO stocks (user_id, stock_name, avg_price) VALUES (?, ?, ?)",
        (user_id, stock_name.upper(), avg_price)
    )
    conn.commit()
    stock_id = cursor.lastrowid
    conn.close()
    return stock_id

def remove_user_stock(stock_id):
    """Remove a stock from the portfolio."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def update_user_stock(stock_id, stock_name, avg_price):
    """Update an existing stock in the portfolio."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE stocks SET stock_name = ?, avg_price = ? WHERE id = ?",
        (stock_name.upper(), avg_price, stock_id)
    )
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

if __name__ == "__main__":
    init_db()
