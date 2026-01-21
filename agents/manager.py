from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a router agent.\n"
        "Decide which agent should handle the user query.\n\n"
        "Return ONLY one word:\n"
        "- viewer (for viewing stock, listing products)\n"
        "- clerk (for selling, adding, updating stock)\n"
    ),
    ("human", "{query}")
])

chain = prompt | llm


def manager_agent(query: str) -> str:
    response = chain.invoke({"query": query})
    decision = response.content.lower().strip()

    # Hard safety guard
    if decision not in ("viewer", "clerk"):
        # heuristic fallback
        if any(word in query.lower() for word in ["sell", "add", "update"]):
            return "clerk"
        return "viewer"

    return decision
