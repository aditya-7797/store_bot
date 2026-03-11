from tools.inventory_tools import get_stock, get_all_products, extract_product_name


def librarian_agent(state: dict) -> dict:
    query = state["query"]

    # Handle "list all products" requests
    if "list" in query.lower() or ("all" in query.lower() and "products" in query.lower()):
        products = get_all_products()
        if not products:
            state["response"] = "No products in inventory."
        else:
            response = "Products in inventory:\n"
            for name, stock in products:
                response += f"- {name}: {stock} units\n"
            state["response"] = response.strip()
        return state

    # Handle single product stock check - use improved extraction
    product = extract_product_name(query)
    
    if not product:
        state["response"] = "Please specify a product name."
        return state

    result = get_stock(product)

    if result is None or result == 0:
       state["response"] = f"No product named '{product}' found in stock."
    else:
       state["response"] = f"There are {result} {product} available in stock."
    
    return state

