import random
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("inventory.db")
cur = conn.cursor()

with open("schema.sql") as f:
    cur.executescript(f.read())

# 30 related general-store products for useful Apriori patterns
products = [
    ("milk packet", 220),
    ("bread loaf", 180),
    ("butter", 120),
    ("jam", 95),
    ("eggs dozen", 140),
    ("tea powder", 160),
    ("coffee jar", 90),
    ("sugar", 210),
    ("salt", 200),
    ("rice bag", 130),
    ("wheat flour", 125),
    ("cooking oil", 150),
    ("turmeric powder", 110),
    ("chili powder", 105),
    ("coriander powder", 100),
    ("maggi noodles", 240),
    ("tomato ketchup", 115),
    ("potato chips", 260),
    ("soft drink", 190),
    ("biscuits", 230),
    ("chocolate", 170),
    ("toothpaste", 150),
    ("toothbrush", 130),
    ("bath soap", 210),
    ("shampoo sachet", 220),
    ("detergent powder", 155),
    ("dishwash liquid", 120),
    ("tissue pack", 145),
    ("blue pen", 260),
    ("notebook", 180),
]

# Clear existing products and sales, then insert clean baseline
cur.execute("DELETE FROM sales")
cur.execute("DELETE FROM products")
cur.executemany("INSERT INTO products (name, stock) VALUES (?, ?)", products)

# Build product id map
cur.execute("SELECT id, name FROM products")
product_rows = cur.fetchall()
product_to_id = {name: pid for pid, name in product_rows}

price_map = {
    "milk packet": 30.0,
    "bread loaf": 40.0,
    "butter": 55.0,
    "jam": 70.0,
    "eggs dozen": 72.0,
    "tea powder": 140.0,
    "coffee jar": 180.0,
    "sugar": 48.0,
    "salt": 22.0,
    "rice bag": 520.0,
    "wheat flour": 310.0,
    "cooking oil": 165.0,
    "turmeric powder": 35.0,
    "chili powder": 42.0,
    "coriander powder": 38.0,
    "maggi noodles": 14.0,
    "tomato ketchup": 95.0,
    "potato chips": 20.0,
    "soft drink": 40.0,
    "biscuits": 10.0,
    "chocolate": 30.0,
    "toothpaste": 95.0,
    "toothbrush": 35.0,
    "bath soap": 32.0,
    "shampoo sachet": 2.0,
    "detergent powder": 110.0,
    "dishwash liquid": 85.0,
    "tissue pack": 75.0,
    "blue pen": 12.0,
    "notebook": 45.0,
}

# Co-purchase bundles to make Apriori useful
bundle_groups = [
    ["milk packet", "bread loaf", "butter", "jam"],
    ["tea powder", "sugar", "biscuits"],
    ["maggi noodles", "tomato ketchup", "soft drink", "potato chips"],
    ["toothpaste", "toothbrush", "bath soap", "shampoo sachet"],
    ["rice bag", "wheat flour", "cooking oil", "salt"],
    ["turmeric powder", "chili powder", "coriander powder"],
    ["blue pen", "notebook", "tissue pack"],
    ["detergent powder", "dishwash liquid", "bath soap"],
]

all_products = [name for name, _ in products]
random.seed(42)

base_date = datetime.now() - timedelta(days=180)
sales_rows = []

# Generate 1000 basket transactions (1 to 5 unique products per transaction)
for tx_num in range(1, 1001):
    transaction_id = f"TX{tx_num:05d}"
    sale_time = base_date + timedelta(
        days=random.randint(0, 180),
        hours=random.randint(8, 21),
        minutes=random.randint(0, 59),
    )

    basket = set()

    # 70% chance to include one strong bundle
    if random.random() < 0.70:
        primary_group = random.choice(bundle_groups)
        basket.update(random.sample(primary_group, k=random.randint(1, min(3, len(primary_group)))))

    # 25% chance to include another cross-category bundle item
    if random.random() < 0.25:
        secondary_group = random.choice(bundle_groups)
        basket.update(random.sample(secondary_group, k=1))

    # Fill remaining basket items with random products
    target_size = random.randint(1, 5)
    while len(basket) < target_size:
        basket.add(random.choice(all_products))

    for product_name in basket:
        quantity = random.randint(1, 4)
        unit_price = price_map[product_name]
        jittered_price = round(unit_price * random.uniform(0.95, 1.08), 2)
        sales_rows.append(
            (
                transaction_id,
                product_to_id[product_name],
                quantity,
                jittered_price,
                sale_time.strftime("%Y-%m-%d %H:%M:%S"),
            )
        )

cur.executemany(
    """
    INSERT INTO sales (transaction_id, product_id, quantity, price, created_at)
    VALUES (?, ?, ?, ?, ?)
    """,
    sales_rows,
)

conn.commit()
conn.close()

print(f"Database initialized with {len(products)} products and 1000 transactions")
