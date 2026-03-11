# SmartRetail AI - Intelligent Business Analytics Platform

> AI-powered multi-agent system for retail inventory management, sales forecasting, and business intelligence.

## 🎯 Project Overview

SmartRetail AI transforms traditional general store management into an intelligent, predictive analytics platform using:
- **Multi-Agent AI Architecture** (LangChain + LangGraph)
- **Predictive Analytics** (Time-series forecasting, customer segmentation)
- **Natural Language Interface** (Conversational AI for business queries)
- **Real-time Dashboards** (Streamlit + Plotly visualizations)

## 🏗️ Architecture

```
Frontend (Streamlit)  ←→  Backend (FastAPI)  ←→  AI Agents (LangGraph)
                                 ↓
                          ML Models
                    (Forecasting, Clustering)
                                 ↓
                          Database (PostgreSQL/SQLite)
```

## 📁 Project Structure

```
smartretail-ai/
├── backend/
│   ├── api/              # FastAPI routes
│   ├── models/           # ML models (forecasting, segmentation)
│   ├── database/         # Database connection and schemas
│   ├── config.py         # Configuration settings
│   └── main.py           # FastAPI application
├── frontend/
│   └── dashboard.py      # Streamlit dashboard
├── agents/               # LangGraph AI agents
│   ├── manager.py        # Routing agent
│   ├── librarian.py      # Stock query agent
│   ├── clerk.py          # Inventory operations agent
│   └── (more agents coming in Phase 2-3)
├── graph/
│   └── workflow.py       # LangGraph workflow orchestration
├── tools/                # Agent tools and utilities
│   ├── db.py
│   ├── inventory_tools.py
│   └── voice_tools.py
├── data/                 # Data files
├── notebooks/            # Jupyter notebooks for ML experiments
├── tests/                # Unit tests
├── .env                  # Environment variables
├── requirements-full.txt # All dependencies
└── README-NEW.md         # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL (for Phase 2) or SQLite (development)
- Groq API key (free at console.groq.com)

### Installation

1. **Clone and setup:**
```bash
cd langgraph-multi-agent-chatbot
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

2. **Install dependencies:**
```bash
pip install -r requirements-full.txt
```

3. **Set up environment variables:**
Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=sqlite:///inventory.db
```

4. **Initialize database:**
```bash
python seed.py
```

### Running the Application

**Terminal 1 - Start FastAPI Backend:**
```bash
python backend/main.py
# Runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

**Terminal 2 - Start Streamlit Frontend:**
```bash
streamlit run frontend/dashboard.py
# Runs on http://localhost:8501
```

## 📊 Features

### Phase 1 (Current) ✅
- ✅ Multi-agent AI system (Manager, Librarian, Clerk)
- ✅ Natural language inventory queries
- ✅ FastAPI REST API backend
- ✅ Streamlit dashboard with multiple pages
- ✅ Real-time stock management
- ✅ Voice input support (optional)

### Phase 2 (In Progress) 🚧
- 🚧 Sales transaction tracking
- 🚧 Business analytics dashboard
- 🚧 Profit margin analysis
- 🚧 PostgreSQL migration
- 🚧 Data generation scripts

### Phase 3 (Planned) 📋
- 📋 Sales forecasting (ARIMA/Prophet)
- 📋 Customer segmentation (K-Means)
- 📋 Market basket analysis (Apriori)
- 📋 Anomaly detection
- 📋 Profit optimization recommendations

## 🤖 AI Agents

### Current Agents:
1. **Manager Agent**: Routes queries to appropriate specialized agents
2. **Librarian Agent**: Handles stock availability queries
3. **Clerk Agent**: Manages inventory operations (add/sell)

### Planned Agents (Phase 2-3):
4. **Sales Analytics Agent**: Revenue, profit, trend analysis
5. **Forecasting Agent**: Demand prediction
6. **Customer Intelligence Agent**: Segmentation, RFM analysis
7. **Business Insights Agent**: Market basket, recommendations

## 📖 API Documentation

### Key Endpoints:

**AI Query:**
```bash
POST /api/query
Body: {"query": "How many blue pens in stock?"}
```

**Get Products:**
```bash
GET /api/inventory/products
```

**Update Stock:**
```bash
POST /api/inventory/update
Body: {"product_name": "blue pen", "quantity": 10}
```

**Full API docs:** http://localhost:8000/docs (when backend is running)

## 💡 Example Queries

Natural language queries you can ask:

```
📦 Inventory:
- "How many blue pens in stock?"
- "What products are available?"
- "Add 10 oil bottles"
- "Sell 5 biscuit boxes"

📊 Analytics (Phase 2):
- "Total sales for blue pen in January"
- "Overall profit for oil bottles"
- "Top 5 selling products"

🔮 Forecasting (Phase 3):
- "Predict Maggi sales for next 30 days"
- "Will milk demand increase next month?"

👥 Customers (Phase 3):
- "Which customer segment buys premium products?"
- "Target group for blue pens"
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI, Uvicorn |
| **Frontend** | Streamlit, Plotly |
| **AI/LLM** | LangChain, LangGraph, Groq |
| **ML** | scikit-learn, Prophet, statsmodels |
| **Database** | PostgreSQL (production), SQLite (dev) |
| **Visualization** | Plotly, Matplotlib, Seaborn |

## 📈 Development Roadmap

- [x] Phase 1: Basic multi-agent inventory system (Week 1-2)
- [ ] Phase 2: Analytics and database upgrade (Week 3-5)
- [ ] Phase 3: ML models integration (Week 6-8)
- [ ] Phase 4: Advanced features (Week 9-11)
- [ ] Phase 5: Testing and deployment (Week 12)

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest tests/

# Test individual components
python -m pytest tests/test_agents.py
python -m pytest tests/test_models.py
```

## 📝 Contributing

This is an academic project. For improvements:
1. Create feature branch
2. Make changes
3. Test thoroughly
4. Document changes

## 📄 License

Academic project - All rights reserved

## 👤 Author

[Your Name]
[Your Roll Number]
[Your Institution]

## 🙏 Acknowledgments

- LangChain/LangGraph for multi-agent framework
- Groq for fast LLM inference
- Streamlit for rapid dashboard development

---

**Status:** 🟢 Active Development  
**Version:** 1.0.0  
**Last Updated:** March 2026
