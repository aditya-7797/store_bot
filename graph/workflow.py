from langgraph.graph import StateGraph
from agents.manager import manager_agent
from agents.librarian import librarian_agent
from agents.clerk import clerk_agent
from agents.analytics import analytics_agent

workflow = StateGraph(dict)

workflow.add_node("manager", manager_agent)

workflow.add_node("librarian", librarian_agent)
workflow.add_node("clerk", clerk_agent)
workflow.add_node("analytics", analytics_agent)

workflow.add_conditional_edges(
    "manager",
    lambda state: state["route"],
    {
        "librarian": "librarian",
        "clerk": "clerk",
        "analytics": "analytics",
    }
)

workflow.set_entry_point("manager")

graph = workflow.compile()
