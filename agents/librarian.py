from tools.inventory_tools import get_all_products, get_stock, normalize_product_name


def viewer_agent(query: str):
    query = query.lower().strip()

    # ---- List all products ----
    if "list" in query or "all products" in query:
        products = get_all_products()
        if not products:
            return "Inventory is empty."

        return "\n".join(f"{name}: {stock}" for name, stock in products)

    # ---- Stock query ----
    words = query.split()

    # try last 2 words, then last 1 word (blue pens / pens)
    for size in (2, 1):
        product_name = " ".join(words[-size:])
        product_name = normalize_product_name(product_name)

        stock = get_stock(product_name)
        return f"{stock} in stock"

    return "Product not found"
