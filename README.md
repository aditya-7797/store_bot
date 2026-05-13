# LangGraph Multi-Agent Inventory Chatbot

A multi-agent conversational inventory assistant built with LangGraph and LangChain. The system supports
inventory queries, transactions (add/sell), analytics, forecasting, and a RAG-powered Operations Copilot that
references internal documentation (SOPs and onboarding guide) to answer procedural questions.

This README explains features, architecture, setup, how to run the UI, and where to find the RAG copilot.

**Supported features**
- Multi-agent routing (manager routes to librarian/clerk/analytics/forecast/rag_copilot)
- Inventory operations: check stock, add stock, record sales, and simple guardrails
- Analytics: RFM segmentation, top customers, push/reorder recommendations
- Forecasting hooks (Prophet) for demand estimates
- RAG-based Operations Copilot that cites `docs/SOP_INVENTORY_RECONCILIATION.md` and `docs/ONBOARDING_GUIDE.md`
- Streamlit frontend with text + push-to-talk voice input

## Repository layout (high level)

 - agents/
	 - manager.py         — routing logic
	 - librarian.py       — stock lookups
	 - clerk.py           — add / sell operations
	 - analytics.py       — analytics agent
	 - forecast.py        — forecasting agent
	 - rag_copilot.py     — RAG agent (loads docs, FAISS vector store)

 - graph/
	 - workflow.py        — LangGraph workflow, includes `rag_copilot` node

 - backend/
	 - main.py            — FastAPI app (exposes endpoints, integrates agents)

 - tools/               — helper utilities (inventory_tools, db, analytics)
 - docs/                — documentation: SOP and Onboarding guide (RAG sources)
 - app.py               — Streamlit frontend
 - test_rag_integration.py — integration tests / health checks
 - requirements.txt     — main Python dependencies

## RAG Copilot — where it lives and how it works

 - Code: `agents/rag_copilot.py` — loads and indexes `docs/SOP_INVENTORY_RECONCILIATION.md` and `docs/ONBOARDING_GUIDE.md`.
 - Workflow: `graph/workflow.py` includes `rag_copilot` as a node and `agents/manager.py` routes relevant queries to it.
 - UI: The RAG answers are visible in the Streamlit chat UI (`app.py`) under the page title "📦 Inventory Assistant".
 - Typical RAG queries: "How do I handle negative stock?", "How can I add items to stock?", "Who should we prioritize for promotions?", "What does RFM mean?"

## Quickstart (local development)

Prereqs: Python 3.10+, Git, a virtual environment. Activate your project venv before running commands.

1. Create & activate venv (if not already):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies (vvenv active):

```powershell
pip install -r requirements.txt
# Optional for RAG: faiss-cpu sentence-transformers langchain-huggingface huggingface_hub[hf_xet]
pip install faiss-cpu sentence-transformers langchain-huggingface huggingface_hub[hf_xet]
```

3. Add environment variables (create `.env`):

```
HF_TOKEN=your_huggingface_token_here
# any other secrets (API keys) the project requires
```

4. Run tests (quick integration check):

```powershell
python test_rag_integration.py
```

5. Run the Streamlit frontend (chat UI):

```powershell
.venv\Scripts\Activate.ps1
streamlit run app.py
# then open http://localhost:8501 in your browser
```

6. (Optional) Start backend API:

```powershell
.venv\Scripts\Activate.ps1
python start_backend.py
# FastAPI will be available on http://localhost:8000 by default
```

## Example queries (what to ask in the UI)

Inventory / Clerk:
- "How many milk packets in stock?"
- "Add 10 milk packets"
- "Sell 3 bread loaves"

Analytics / RFM:
- "What does RFM mean?"
- "Who should we prioritize for promotions?"

RAG / SOP (Operations Copilot):
- "How do I handle negative stock?"
- "How do I reconcile inventory at end of day?"

## API Endpoints (selected)

- `GET /` — health check
- `POST /query` — send a natural language query to the workflow (proxied to manager)
- `POST /api/inventory/update` — update stock (used by UI and SOP examples)
- `POST /api/transactions/record` — record a sale transaction

See `backend/main.py` for full route definitions and request models.

## Troubleshooting & notes

- If RAG fails to return context: ensure `docs/` files exist and the vector store is initialized. The first run may download HF models and take time.
- If you see LangChain deprecation warnings for embeddings, install `langchain-huggingface` and set `HF_TOKEN` to speed downloads.
- If Streamlit reloads packages unexpectedly during development, restart the server; some package installs edit site-packages and trigger WatchFiles.

## Testing & development tips

- Use `test_rag_integration.py` to validate imports, routing, vector store creation, and workflow invocation locally.
- Edit `agents/manager.py` to tune routing keywords or add new agents.
- Add documents to `docs/` and restart to include them in the RAG index (or rebuild the FAISS store programmatically).

## Contributing

- Follow the repository style. Add unit tests for new agents and ensure `test_rag_integration.py` passes locally before submitting PRs.

---

If you want, I can also:
- open the running Streamlit UI and run a set of example RAG queries now, or
- create a small README `How To Demo` script that runs a sample conversation automatically.

