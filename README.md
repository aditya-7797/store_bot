# LangGraph Multi-Agent Inventory Chatbot

A multi-agent conversational inventory chatbot built using LangGraph + LangChain, designed to manage shop inventory using natural language queries.
The system supports stock checking, adding items, selling items, and low-stock detection, with optional voice input via Streamlit.

## Features

1️)Multi-Agent Architecture

Manager Agent – Routes user queries to the appropriate agent based on intent.

Librarian Agent – Handles stock availability queries and low-stock detection.

Clerk Agent – Handles inventory operations such as adding and selling items.

2️)Inventory Management

Check item availability

Add new stock

Sell items

3️)Voice + Text Input

Streamlit-based user interface

Optional speech-to-text integration

4️)LLM Powered

Uses Groq LLaMA-3.1-8B-Instant

Deterministic responses (temperature = 0) for consistent output

## Folder Structure

```text
langgraph-multi-agent-chatbot/
│
├── agents/
│   ├── manager.py        # Routes queries to the correct agent
│   ├── librarian.py      # Handles stock queries & low-stock detection
│   └── clerk.py          # Handles add/sell inventory operations
│
├── graph/
│   └── workflow.py       # LangGraph workflow definition
│
├── tools/
│   ├── db.py             # Database connection
│   └── inventory.py     # Inventory CRUD operations
│
├── app.py                # Streamlit application
├── inventory.db          # SQLite database (gitignored)
├── .gitignore
├── README.md
└── requirements.txt
```

## Sample Queries

Inventory Queries

How many blue pens?

Add 3 blue pens

Sell 3 blue pens

## Tech Stack

Python

LangChain

LangGraph

Groq LLM (LLaMA-3.1-8B)

SQLite

Streamlit

## Use Cases

Learning multi-agent systems

Conversational AI demos

Inventory management automation
