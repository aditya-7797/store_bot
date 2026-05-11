from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

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
- "analytics" - for product recommendations, bundle suggestions, association queries like what sells with what
- "forecast" - for predicting future sales, demand forecasting, expected sales next month/week

Respond with ONLY ONE WORD: either "librarian", "clerk", "analytics", or "forecast"

Examples:
- "how many pens do we have?" → librarian
- "add 10 blue pens" → clerk
- "sell 5 bottles" → clerk
- "what's in stock?" → librarian
- "check oil bottle availability" → librarian
- "update stock with 10 markers" → clerk
- "what can I sell with bread loaf" → analytics
- "which products are bought together with tea powder" → analytics
- "recommend bundle for milk packet" → analytics
- "what will be the sales of milk next month?" → forecast
- "predict demand for rice" → forecast
- "how much sugar will sell next week?" → forecast
- "forecast eggs for next 30 days" → forecast
- "expected sales of bread" → forecast"""),
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
        if route in ["librarian", "clerk", "analytics", "forecast"]:
            state["route"] = route
        else:
            # Fallback to librarian if LLM returns something unexpected
            state["route"] = "librarian"
    except Exception as e:
        # Fallback routing if LLM fails
        query_lower = query.lower()
        if (
            "forecast" in query_lower
            or "predict" in query_lower
            or "prediction" in query_lower
            or "next month" in query_lower
            or "next week" in query_lower
            or "expected sales" in query_lower
            or "demand" in query_lower
            or "future sales" in query_lower
        ):
            state["route"] = "forecast"
        elif (
            "sell with" in query_lower
            or "buy with" in query_lower
            or "bought together" in query_lower
            or "recommend" in query_lower
            or "bundle" in query_lower
            or "pair with" in query_lower
        ):
            state["route"] = "analytics"
        elif "add" in query_lower or "sell" in query_lower or "update" in query_lower:
            state["route"] = "clerk"
        else:
            state["route"] = "librarian"
    
    return state

