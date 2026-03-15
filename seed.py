import sqlite3

conn = sqlite3.connect("inventory.db")
cur = conn.cursor()

with open("schema.sql") as f:
    cur.executescript(f.read())

products = [
    ("biscuit box", 30),
    ("blue pen", 100),
    ("oil bottle", 50),
    ("g soap", 60),
]

# Clear existing products and re-insert clean data
cur.execute("DELETE FROM products")
cur.executemany(
    "INSERT INTO products (name, stock) VALUES (?, ?)",
    products
)

conn.commit()
conn.close()

print("Database initialized")
