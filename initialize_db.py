
import sqlite3
conn = sqlite3.connect("inventory.db")
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, stock INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_id TEXT, product_id INTEGER, quantity INTEGER, price REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit()
conn.close()
print("Database reset.")
