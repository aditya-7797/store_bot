from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

# Classification prompt for intelligent routing
routing_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a routing assistant for an inventory management system.
    
Analyze the user's query and classify it into ONE of these categories:
- "librarian" - for checking stock levels, availability, listing products
- "clerk" - for adding items to stock, selling/removing items from stock

Respond with ONLY ONE WORD: either "librarian" or "clerk"

Examples:
- "how many pens do we have?" → librarian
- "add 10 blue pens" → clerk
- "sell 5 bottles" → clerk
- "what's in stock?" → librarian
- "check oil bottle availability" → librarian
- "update stock with 10 markers" → clerk"""),
    ("user", "{query}")
])

routing_chain = routing_prompt | llm

def manager_agent(state: dict):
    query = state["query"]
    
    try:
        # Use LLM for intelligent routing
        result = routing_chain.invoke({"query": query})
        route = result.content.strip().lower()
        
        # Validate the route
        if route in ["librarian", "clerk"]:
            state["route"] = route
        else:
            # Fallback to librarian if LLM returns something unexpected
            state["route"] = "librarian"
    except Exception as e:
        # Fallback routing if LLM fails
        query_lower = query.lower()
        if "add" in query_lower or "sell" in query_lower or "update" in query_lower:
            state["route"] = "clerk"
        else:
            state["route"] = "librarian"
    
    return state

