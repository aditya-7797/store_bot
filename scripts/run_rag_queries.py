"""Run a few test queries against the workflow graph and print responses.
"""
import sys
import os
import json

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.workflow import graph

queries = [
    "How do I handle negative stock?",
    "How can I add items to stock?",
    "Who should we prioritize for promotions?",
    "What does RFM mean?",
    "How do I reconcile inventory at end of day?",
]

for q in queries:
    print("\n---")
    print(f"Query: {q}")
    try:
        final = graph.invoke({"query": q})
        route = final.get("route")
        response = final.get("response")
        print(f"Route: {route}")
        print("Response:")
        print(response)
    except Exception as e:
        print(f"Error invoking graph: {e}")

print("\nDone.")
