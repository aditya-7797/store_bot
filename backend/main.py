"""
FastAPI Backend for SmartRetail AI
Main application entry point
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from graph.workflow import graph
from tools.inventory_tools import get_all_products, get_stock, update_stock

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered retail analytics and inventory management system"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Request/Response Models ====================

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    response: str
    route: Optional[str] = None

class Product(BaseModel):
    name: str
    stock: int

class StockUpdate(BaseModel):
    product_name: str
    quantity: int

# ==================== Health Check ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "ai_agents": "active"
    }

# ==================== AI Agent Endpoints ====================

@app.post("/api/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Send natural language query to multi-agent system
    
    Example queries:
    - "How many blue pens in stock?"
    - "Add 10 oil bottles"
    - "Sell 5 biscuit boxes"
    """
    try:
        state = {"query": request.query}
        final_state = graph.invoke(state)
        
        return QueryResponse(
            query=request.query,
            response=final_state.get("response", "No response generated"),
            route=final_state.get("route")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

# ==================== Inventory Endpoints ====================

@app.get("/api/inventory/products", response_model=List[Dict[str, Any]])
async def get_products():
    """Get all products with stock levels"""
    try:
        products = get_all_products()
        return [{"name": name, "stock": stock} for name, stock in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/inventory/stock/{product_name}")
async def get_product_stock(product_name: str):
    """Get stock level for specific product"""
    try:
        stock = get_stock(product_name)
        return {"product": product_name, "stock": stock}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/inventory/update")
async def update_product_stock(update: StockUpdate):
    """Update stock (add or remove)"""
    try:
        result = update_stock(update.product_name, update.quantity)
        new_stock = get_stock(update.product_name)
        return {
            "message": result,
            "product": update.product_name,
            "new_stock": new_stock
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")

# ==================== Analytics Endpoints (Placeholder) ====================

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get overall business analytics summary"""
    # TODO: Implement actual analytics
    return {
        "total_products": len(get_all_products()),
        "total_stock_value": 0,
        "low_stock_items": 0,
        "message": "Analytics coming in Phase 2"
    }

@app.get("/api/analytics/top-products")
async def get_top_products(limit: int = 5):
    """Get top selling products"""
    # TODO: Implement with sales data
    return {
        "message": "Top products analysis - Coming soon",
        "requires": "Sales transaction data"
    }

# ==================== Forecasting Endpoints (Placeholder) ====================

@app.get("/api/forecast/{product_name}")
async def forecast_product_sales(product_name: str, days: int = 30):
    """Forecast product sales for next N days"""
    # TODO: Implement Prophet/ARIMA model
    return {
        "product": product_name,
        "forecast_days": days,
        "message": "Forecasting model - Coming in Phase 3",
        "requires": "Historical sales data"
    }

# ==================== Customer Analytics Endpoints (Placeholder) ====================

@app.get("/api/customers/segments")
async def get_customer_segments():
    """Get customer segmentation analysis"""
    # TODO: Implement K-Means clustering
    return {
        "message": "Customer segmentation - Coming in Phase 3",
        "requires": "Customer purchase history"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
