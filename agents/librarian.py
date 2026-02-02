from tools.inventory_tools import get_stock

    # existing stock logic...

def librarian_agent(state: dict) -> dict:
    query = state["query"].lower()

    product = (
        query.replace("how many", "")
        .replace("stock", "")
        .strip()
    )

    result = get_stock(product)

    if result is None:
       state["response"] = f"No product named '{product}' found."
    else:
       state["response"] = f"There are {result} {product} available in stock."
    
    return state

