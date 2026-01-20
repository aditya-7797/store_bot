import sqlite3

conn = sqlite3.connect("inventory.db")
cur = conn.cursor()

with open("schema.sql") as f:
    cur.executescript(f.read())

products = [
    ("blue pen", 100),
    ("oil bottle", 50),
    ("biscuit box", 30)
]

cur.executemany(
    "INSERT OR IGNORE INTO products (name, stock) VALUES (?, ?)",
    products
)

conn.commit()
conn.close()

print("Database initialized")
