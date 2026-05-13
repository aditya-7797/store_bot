from langgraph.graph import StateGraph
from agents.manager import manager_agent
from agents.librarian import librarian_agent
from agents.clerk import clerk_agent
from agents.analytics import analytics_agent
from agents.forecast import forecast_agent
from agents.rag_copilot import rag_copilot

workflow = StateGraph(dict)

workflow.add_node("manager", manager_agent)

workflow.add_node("librarian", librarian_agent)
workflow.add_node("clerk", clerk_agent)
workflow.add_node("analytics", analytics_agent)
workflow.add_node("forecast", forecast_agent)
workflow.add_node("rag_copilot", rag_copilot)

workflow.add_conditional_edges(
    "manager",
    lambda state: state["route"],
    {
        "librarian": "librarian",
        "clerk": "clerk",
        "analytics": "analytics",
        "forecast": "forecast",
        "rag_copilot": "rag_copilot",
    }
)

workflow.set_entry_point("manager")

graph = workflow.compile()
