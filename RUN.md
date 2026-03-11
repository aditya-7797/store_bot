# 🚀 Quick Start Guide - SmartRetail AI

## Step-by-Step Setup

### 1️⃣ Activate Virtual Environment
```powershell
# You already have .venv, so just activate it
.\.venv\Scripts\Activate.ps1
```

### 2️⃣ Install New Dependencies
```powershell
pip install fastapi uvicorn pydantic plotly
```

### 3️⃣ Make Sure Database is Ready
```powershell
python seed.py
```

### 4️⃣ Start Backend (Terminal 1)
```powershell
# Run FastAPI backend
python backend/main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Test it:** Open http://localhost:8000/docs in browser

### 5️⃣ Start Frontend (Terminal 2)
```powershell
# Open a NEW PowerShell terminal
cd C:\MP2\langgraph-multi-agent-chatbot
.\.venv\Scripts\Activate.ps1

# Run Streamlit dashboard
streamlit run frontend/dashboard.py
```

You should see:
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

## ✅ What You Should See

**Backend (Port 8000):**
- FastAPI Swagger docs at http://localhost:8000/docs
- Health check at http://localhost:8000/health

**Frontend (Port 8501):**
- Professional dashboard with multiple pages
- Navigation sidebar
- KPI metrics
- Charts and tables
- AI assistant chat

## 🧪 Test the System

### Test 1: Health Check
Open browser: http://localhost:8000/health

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "ai_agents": "active"
}
```

### Test 2: API Query
In Swagger docs (http://localhost:8000/docs):
1. Click on `POST /api/query`
2. Click "Try it out"
3. Enter: `{"query": "how many blue pens"}`
4. Click "Execute"

### Test 3: Dashboard
1. Go to http://localhost:8501
2. Navigate between pages in sidebar
3. Try "AI Assistant" page
4. Ask: "How many oil bottles in stock?"

## 🐛 Troubleshooting

**Problem:** "Cannot connect to backend"
**Solution:** Make sure FastAPI is running on port 8000

**Problem:** "Module not found"
**Solution:** 
```powershell
pip install -r requirements-full.txt
```

**Problem:** ImportError with agents/graph
**Solution:** The project structure is backward compatible

## 📊 What's Different Now?

**Before (app.py):**
- All-in-one Streamlit app
- No API
- Limited features

**Now (FastAPI + Streamlit):**
- ✅ Separated backend/frontend
- ✅ RESTful API
- ✅ Multiple dashboard pages
- ✅ Professional architecture
- ✅ Ready for ML models
- ✅ Scalable design

## 🎯 Next Steps

1. ✅ Run both services (backend + frontend)
2. ✅ Test all 6 dashboard pages
3. ✅ Try AI assistant
4. 📋 Start Phase 2: Add sales tracking
5. 📋 Implement ML models

## 💡 Pro Tips

**Keep both terminals open:**
- Terminal 1: FastAPI backend (python backend/main.py)
- Terminal 2: Streamlit frontend (streamlit run frontend/dashboard.py)

**Auto-reload enabled:**
- Both FastAPI and Streamlit auto-reload on code changes
- No need to restart after editing

**API Testing:**
- Use Swagger UI: http://localhost:8000/docs
- Or use Postman/curl
- Or use requests library in Python

---

**You're now running a professional FastAPI + Streamlit architecture! 🎉**
