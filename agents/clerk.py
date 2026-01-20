from tools.inventory_tools import get_all_products, get_stock

def clerk_agent(query: str):
    q = query.lower()

    if "all" in q:
        return get_all_products()

    if "blue pen" in q:
        return get_stock("blue pen")

    return "I can help with inventory-related questions."
