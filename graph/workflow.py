from typing import TypedDict

from langgraph.graph import StateGraph, END

from agents.manager import manager_agent
from agents.librarian import viewer_agent
from agents.clerk import clerk_agent


# ---- State Definition ----
class AgentState(TypedDict):
    query: str
    result: str


# ---- Nodes ----
def route_node(state: AgentState) -> AgentState:
    decision = manager_agent(state["query"])
    return {"query": state["query"], "result": decision}


def viewer_node(state: AgentState) -> AgentState:
    response = viewer_agent(state["query"])
    return {"query": state["query"], "result": response}


def clerk_node(state: AgentState) -> AgentState:
    response = clerk_agent(state["query"])
    return {"query": state["query"], "result": response}


# ---- Graph ----
graph = StateGraph(AgentState)

graph.add_node("router", route_node)
graph.add_node("viewer", viewer_node)
graph.add_node("clerk", clerk_node)

graph.set_entry_point("router")

graph.add_conditional_edges(
    "router",
    lambda state: state["result"],
    {
        "viewer": "viewer",
        "clerk": "clerk",
    },
)

graph.add_edge("viewer", END)
graph.add_edge("clerk", END)

workflow = graph.compile()
