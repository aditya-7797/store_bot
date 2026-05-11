"""
Seed product prices into the database for RFM estimation.
Run this once to initialize prices for all products.
"""
import sqlite3
from backend.config import settings

def seed_product_prices():
    """Initialize product prices in the database if not already set."""
    conn = sqlite3.connect(settings.SQLITE_DB)
    cur = conn.cursor()
    
    # Check if prices already exist in sales table
    cur.execute("SELECT COUNT(*) FROM sales WHERE price IS NOT NULL AND price > 0")
    existing_prices = cur.fetchone()[0]
    
    if existing_prices >= 100:
        print(f"Prices already initialized ({existing_prices} sales with valid prices)")
        conn.close()
        return
    
    # Define reasonable prices for Indian general store items
    price_catalog = {
        "bread": 30,
        "milk": 45,
        "eggs": 60,  # per dozen
        "butter": 120,
        "cheese": 180,
        "yogurt": 40,
        "rice": 50,
        "wheat flour": 35,
        "sugar": 40,
        "salt": 15,
        "oil": 110,
        "spices": 80,
        "tea": 180,
        "coffee": 200,
        "biscuits": 25,
        "chocolate": 30,
        "chips": 20,
        "juice": 35,
        "water": 20,
        "soda": 30,
        "snacks": 40,
        "nuts": 200,
        "fruits": 60,
        "vegetables": 50,
        "yogurt": 40,
        "paneer": 250,
        "meat": 300,
        "fish": 250,
        "dal": 80,
        "flour": 35,
    }
    
    # Get all products and assign prices
    cur.execute("SELECT id, name FROM products")
    products = cur.fetchall()
    
    updates = 0
    for product_id, product_name in products:
        norm_name = product_name.lower().strip()
        
        # Try to find matching price
        price = None
        for key, val in price_catalog.items():
            if key in norm_name or norm_name in key:
                price = val
                break
        
        if price is None:
            # Default price based on product category heuristics
            if "salt" in norm_name or "spice" in norm_name:
                price = 15
            elif "oil" in norm_name or "butter" in norm_name:
                price = 100
            elif "tea" in norm_name or "coffee" in norm_name:
                price = 150
            elif "fruit" in norm_name or "vegetable" in norm_name:
                price = 50
            else:
                price = 50  # default
        
        # Update product prices in sales table (for future calculations)
        cur.execute(
            "UPDATE sales SET price = ? WHERE product_id = ? AND (price IS NULL OR price = 0)",
            (price, product_id)
        )
        updates += cur.rowcount
    
    conn.commit()
    print(f"Seeded prices for {len(products)} products, updated {updates} sales records")
    conn.close()

if __name__ == "__main__":
    seed_product_prices()
