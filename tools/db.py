import sqlite3
import os

# Point to the database in the root folder, not the tools folder
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inventory.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        stock INTEGER DEFAULT 0 CHECK(stock >= 0)
    )
    """)
    return conn
