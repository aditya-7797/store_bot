"""
Improved build_product_price_map with fallback pricing.
This replaces the old function in customer_analytics.py.
"""

import pandas as pd
from tools.db import get_connection

FALLBACK_PRICES = {
    "bread": 30, "milk": 45, "eggs": 60, "butter": 120, "cheese": 180,
    "yogurt": 40, "rice": 50, "wheat flour": 35, "sugar": 40, "salt": 15,
    "oil": 110, "spices": 80, "tea": 180, "coffee": 200, "biscuits": 25,
    "chocolate": 30, "chips": 20, "juice": 35, "water": 20, "soda": 30,
    "snacks": 40, "nuts": 200, "fruits": 60, "vegetables": 50,
    "paneer": 250, "meat": 300, "fish": 250, "dal": 80, "flour": 35,
}

def build_product_price_map_new() -> dict[int, float]:
    """Estimate unit prices for each product from sales table with fallback pricing."""
    # First, try to get prices from sales table
    query = """
        SELECT product_id, AVG(price) AS avg_price
        FROM sales
        WHERE product_id IS NOT NULL AND price IS NOT NULL AND price > 0
        GROUP BY product_id
    """
    conn = get_connection()
    try:
        price_df = pd.read_sql_query(query, conn)
        # Also get all products for fallback
        products_df = pd.read_sql_query("SELECT id, name FROM products", conn)
    finally:
        conn.close()

    # Build map from sales data
    price_map = {}
    if not price_df.empty:
        price_df["product_id"] = pd.to_numeric(price_df["product_id"], errors="coerce")
        price_df["avg_price"] = pd.to_numeric(price_df["avg_price"], errors="coerce")
        price_df = price_df.dropna(subset=["product_id", "avg_price"])
        price_map = {
            int(row.product_id): float(row.avg_price)
            for row in price_df.itertuples(index=False)
        }
    
    # For products with no sales history, use fallback pricing based on product name
    if not products_df.empty:
        for _, row in products_df.iterrows():
            product_id = int(row["id"])
            if product_id not in price_map:
                product_name = str(row["name"]).lower().strip()
                # Try to find matching fallback price
                fallback_price = 50.0  # default
                for key, val in FALLBACK_PRICES.items():
                    if key in product_name or product_name in key:
                        fallback_price = float(val)
                        break
                price_map[product_id] = fallback_price
    
    return price_map
