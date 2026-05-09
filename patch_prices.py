"""
Patch script to fix build_product_price_map() in customer_analytics.py.
Adds fallback pricing for products without sales history.
"""

import re

file_path = r"c:\MP2\langgraph-multi-agent-chatbot\tools\customer_analytics.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the build_product_price_map function
old_function = '''def build_product_price_map() -> dict[int, float]:
    """Estimate unit prices for each product from the live sales table."""
    query = """
        SELECT product_id, AVG(price) AS avg_price
        FROM sales
        WHERE product_id IS NOT NULL AND price IS NOT NULL
        GROUP BY product_id
    """
    conn = get_connection()
    try:
        price_df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    if price_df.empty:
        return {}

    price_df["product_id"] = pd.to_numeric(price_df["product_id"], errors="coerce")
    price_df["avg_price"] = pd.to_numeric(price_df["avg_price"], errors="coerce")
    price_df = price_df.dropna(subset=["product_id", "avg_price"])
    return {
        int(row.product_id): float(row.avg_price)
        for row in price_df.itertuples(index=False)
    }'''

new_function = '''def build_product_price_map() -> dict[int, float]:
    """Estimate unit prices for each product from sales table with fallback pricing."""
    FALLBACK_PRICES = {
        "bread": 30, "milk": 45, "eggs": 60, "butter": 120, "cheese": 180,
        "yogurt": 40, "rice": 50, "wheat flour": 35, "sugar": 40, "salt": 15,
        "oil": 110, "spices": 80, "tea": 180, "coffee": 200, "biscuits": 25,
        "chocolate": 30, "chips": 20, "juice": 35, "water": 20, "soda": 30,
        "snacks": 40, "nuts": 200, "fruits": 60, "vegetables": 50,
        "paneer": 250, "meat": 300, "fish": 250, "dal": 80, "flour": 35,
    }
    
    query = """
        SELECT product_id, AVG(price) AS avg_price
        FROM sales
        WHERE product_id IS NOT NULL AND price IS NOT NULL AND price > 0
        GROUP BY product_id
    """
    conn = get_connection()
    try:
        price_df = pd.read_sql_query(query, conn)
        products_df = pd.read_sql_query("SELECT id, name FROM products", conn)
    finally:
        conn.close()

    price_map = {}
    if not price_df.empty:
        price_df["product_id"] = pd.to_numeric(price_df["product_id"], errors="coerce")
        price_df["avg_price"] = pd.to_numeric(price_df["avg_price"], errors="coerce")
        price_df = price_df.dropna(subset=["product_id", "avg_price"])
        price_map = {
            int(row.product_id): float(row.avg_price)
            for row in price_df.itertuples(index=False)
        }
    
    # Fallback: assign prices based on product names
    if not products_df.empty:
        for _, row in products_df.iterrows():
            product_id = int(row["id"])
            if product_id not in price_map:
                product_name = str(row["name"]).lower().strip()
                fallback_price = 50.0
                for key, val in FALLBACK_PRICES.items():
                    if key in product_name or product_name in key:
                        fallback_price = float(val)
                        break
                price_map[product_id] = fallback_price
    
    return price_map'''

if old_function in content:
    content = content.replace(old_function, new_function)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Successfully patched build_product_price_map()")
else:
    print("❌ Could not find the function to replace")
