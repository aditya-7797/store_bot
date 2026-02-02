*LangGraph Multi-Agent Inventory Chatbot
A multi-agent conversational chatbot built using LangGraph + LangChain, designed to manage shop inventory using natural language queries.
The system supports stock checking, adding items, selling items, and low-stock detection, with optional voice input via Streamlit.

*Features

1)Multi-Agent Architecture

Manager Agent – routes user queries to the correct agent
Librarian Agent – handles stock queries & low-inventory questions
Clerk Agent – handles add/sell inventory operations

2)Inventory Management

Check item availability
Add new stock
Sell items

3)Voice + Text Input
Streamlit UI
Optional speech-to-text integration

4)LLM Powered
Uses Groq LLaMA-3.1-8B-Instant
Deterministic responses (temperature=0)

*FOLDER STRUCTURE
langgraph-multi-agent-chatbot/
│
├── agents/
│   ├── manager.py        # Routes queries to correct agent
│   ├── librarian.py      # Handles inventory queries & low stock
│   └── clerk.py          # Handles add/sell actions
│
├── graph/
│   └── workflow.py       # LangGraph workflow definition
│
├── tools/
│   └── inventory.py      # SQLite inventory operations
│
├── app.py                # Streamlit application
├── inventory.db          # SQLite DB (ignored in git)
├── .gitignore
├── README.md
└── requirements.txt

Inventory Queries
How many blue pens?
sell 3 blue pens.
add 3 blue pens?

*Tech Stack
Python
LangChain
LangGraph
Groq LLM (LLaMA-3.1-8B)
SQLite
Streamlit
