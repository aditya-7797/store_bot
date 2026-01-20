from tools.db import get_connection

def get_all_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    data = cur.fetchall()
    conn.close()
    return data

def get_stock(product_name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT stock FROM products WHERE name = ?",
        (product_name,)
    )
    result = cur.fetchone()
    conn.close()
    return result

