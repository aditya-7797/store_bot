from tools.inventory_tools import update_stock


def clerk_agent(query: str):
    query = query.lower().strip()
    words = query.split()

    action = None
    if "sell" in words:
        action = "sell"
    elif "add" in words:
        action = "add"

    if not action:
        return "Could not understand command"

    # extract quantity
    qty = None
    for word in words:
        if word.isdigit():
            qty = int(word)
            break

    if qty is None:
        return "Please specify a quantity."

    # extract product name (everything after qty)
    qty_index = words.index(str(qty))
    product = " ".join(words[qty_index + 1:])

    if not product:
        return "Please specify a product."

    if action == "sell":
        return update_stock(product, -qty)

    if action == "add":
        return update_stock(product, qty)
