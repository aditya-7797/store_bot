from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

def manager_agent(state: dict):
    query = state["query"].lower()

    if "how many" in query or "available" in query:
        state["route"] = "librarian"
    elif "add" in query or "sell" in query:
        state["route"] = "clerk"
    else:
        state["route"] = "librarian"

    return state

