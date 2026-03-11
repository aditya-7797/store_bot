from tools.inventory_tools import get_stock, update_stock, extract_product_name
import re

def clerk_agent(state: dict):
    query = state["query"]

    # Extract quantity
    numbers = re.findall(r'\d+', query)
    if not numbers:
        state["response"] = "Please specify a quantity (number)."
        return state
    
    quantity = int(numbers[0])

    # Extract product name
    product = extract_product_name(query)
    
    if not product:
        state["response"] = "Please specify a product name."
        return state

    if "add" in query.lower():
        update_stock(product, quantity)
        stock = get_stock(product)
        state["response"] = f"Added {quantity} {product}. Current stock: {stock}."
        return state

    if "sell" in query.lower():
        stock = get_stock(product)

        if stock < quantity:
            state["response"] = f"Only {stock} {product} available. Cannot sell {quantity}."
            return state

        update_stock(product, -quantity)
        state["response"] = f"Sold {quantity} {product}. Remaining stock: {stock - quantity}."
        return state

    state["response"] = "I can only add or sell products."
    return state
