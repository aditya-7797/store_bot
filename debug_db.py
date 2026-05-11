import sqlite3
from pathlib import Path
from backend.config import settings

db_path = settings.SQLITE_DB
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check sales table
print("=== SALES TABLE ===")
cur.execute("SELECT COUNT(*) FROM sales")
print(f"Total sales rows: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM sales WHERE price IS NOT NULL AND price > 0")
print(f"Sales with price > 0: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM sales WHERE price IS NULL OR price = 0")
print(f"Sales with NULL or 0 price: {cur.fetchone()[0]}")

print("\nSample sales rows:")
cur.execute("SELECT product_id, quantity, price, created_at FROM sales LIMIT 5")
for row in cur.fetchall():
    print(f"  product_id={row[0]}, qty={row[1]}, price={row[2]}, date={row[3]}")

# Check products table
print("\n=== PRODUCTS TABLE ===")
cur.execute("SELECT COUNT(*) FROM products")
print(f"Total products: {cur.fetchone()[0]}")

print("\nSample products:")
cur.execute("SELECT id, name, stock FROM products LIMIT 5")
for row in cur.fetchall():
    print(f"  id={row[0]}, name={row[1]}, stock={row[2]}")

conn.close()
