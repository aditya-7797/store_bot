from tools.db import get_connection


# ---------- Helper ----------
def normalize_product_name(name: str) -> str:
    name = name.lower().strip()
    # simple normalization for pen / pens
    if name.endswith("pen") and not name.endswith("pens"):
        return name + "s"
    return name


# ---------- Read Operations ----------
def get_all_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, stock FROM products ORDER BY name")
    data = cur.fetchall()
    conn.close()
    return data


def get_stock(product_name: str):
    product_name = normalize_product_name(product_name)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT stock FROM products WHERE name = ?", (product_name,))
    result = cur.fetchone()
    conn.close()

    return result[0] if result else 0


# ---------- Write Operations ----------
def update_stock(product_name: str, quantity: int):
    product_name = normalize_product_name(product_name)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT stock FROM products WHERE name = ?", (product_name,))
    result = cur.fetchone()

    if result:
        current_stock = result[0]
        new_stock = current_stock + quantity

        if new_stock < 0:
            conn.close()
            return (
                f"Cannot sell {abs(quantity)} {product_name}. "
                f"Only {current_stock} in stock."
            )

        cur.execute(
            "UPDATE products SET stock = ? WHERE name = ?",
            (new_stock, product_name),
        )
    else:
        if quantity < 0:
            conn.close()
            return f"Cannot sell {abs(quantity)} {product_name}. Product does not exist."

        cur.execute(
            "INSERT INTO products (name, stock) VALUES (?, ?)",
            (product_name, quantity),
        )

    conn.commit()
    conn.close()
    return "Stock updated"

def cleanup_duplicates():
    conn = get_connection()
    cur = conn.cursor()

    # Fetch all products
    cur.execute("SELECT name, stock FROM products")
    rows = cur.fetchall()

    normalized = {}

    for name, stock in rows:
        norm_name = normalize_product_name(name)
        normalized[norm_name] = normalized.get(norm_name, 0) + stock

    # Reset table
    cur.execute("DELETE FROM products")

    # Insert normalized rows
    for name, stock in normalized.items():
        cur.execute(
            "INSERT INTO products (name, stock) VALUES (?, ?)",
            (name, stock)
        )

    conn.commit()
    conn.close()
