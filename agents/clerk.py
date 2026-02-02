from tools.inventory_tools import get_stock, update_stock
def clerk_agent(state: dict):
    query = state["query"].lower()

    quantity = int([s for s in query.split() if s.isdigit()][0])

    if "add" in query:
        product = query.replace("add", "").replace(str(quantity), "").strip()
        update_stock(product, quantity)
        stock = get_stock(product)
        state["response"] = f"Added {quantity} {product}. Current stock: {stock}."
        return state

    if "sell" in query:
        product = query.replace("sell", "").replace(str(quantity), "").strip()
        stock = get_stock(product)

        if stock < quantity:
            state["response"] = f"Only {stock} {product} available. Cannot sell {quantity}."
            return state

        update_stock(product, -quantity)
        state["response"] = f"Sold {quantity} {product}. Remaining stock: {stock - quantity}."
        return state

    state["response"] = "I can only add or sell products."
    return state
