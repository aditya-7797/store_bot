"""
FastAPI Backend for SmartRetail AI
Main application entry point
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import sqlite3
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from backend.models.apriori_analysis import get_apriori_rules
from graph.workflow import graph
from tools.customer_analytics import append_customer_transaction, build_product_price_map, build_sales_trend, build_top_selling_products, customer_summary_payload
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

class SalesTransactionRequest(BaseModel):
    customer_id: int
    product_name: str
    quantity: int
    purchase_date: Optional[str] = None
    transaction_id: Optional[str] = None
    unit_price: Optional[float] = None

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

@app.post("/api/transactions/record")
async def record_transaction(request: SalesTransactionRequest):
    """Record a live transaction into the sales table and customer transaction CSV."""
    try:
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="quantity must be greater than 0")

        product_name = request.product_name.strip().lower()
        conn = None
        try:
            conn = sqlite3.connect(settings.SQLITE_DB)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("SELECT id, stock, name FROM products WHERE lower(name) = lower(?)", (product_name,))
            product_row = cur.fetchone()
            if not product_row:
                raise HTTPException(status_code=404, detail=f"Product not found: {request.product_name}")

            product_id = int(product_row["id"])
            current_stock = int(product_row["stock"])
            if current_stock < request.quantity:
                raise HTTPException(status_code=400, detail=f"Not enough stock for {request.product_name}. Available: {current_stock}")

            price_lookup = build_product_price_map()
            if request.unit_price is not None:
                unit_price = float(request.unit_price)
            else:
                # If we have a historical price for this product use it, otherwise leave as NULL
                if product_id in price_lookup:
                    unit_price = float(price_lookup.get(product_id))
                else:
                    unit_price = None

            transaction_id = request.transaction_id or f"TX-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:18]}"
            purchase_date = request.purchase_date or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            cur.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (request.quantity, product_id),
            )
            cur.execute(
                "INSERT INTO sales (transaction_id, product_id, quantity, price, created_at) VALUES (?, ?, ?, ?, ?)",
                (transaction_id, product_id, request.quantity, unit_price, purchase_date),
            )
            conn.commit()
        finally:
            if conn is not None:
                conn.close()

        append_customer_transaction({
            "transaction_id": transaction_id,
            "customer_id": request.customer_id,
            "product_id": product_id,
            "quantity": request.quantity,
            "purchase_date": purchase_date,
            "price": unit_price,
        })

        return {
            "message": "Transaction recorded successfully",
            "transaction_id": transaction_id,
            "customer_id": request.customer_id,
            "product_id": product_id,
            "product_name": request.product_name,
            "quantity": request.quantity,
            "unit_price": unit_price,
            "purchase_date": purchase_date,
            "remaining_stock": current_stock - request.quantity,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction record error: {str(e)}")


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


@app.get("/api/analytics/sales-trend")
async def get_sales_trend():
    """Return daily sales trend from the SQLite sales table."""
    try:
        trend = build_sales_trend()
        return {"trend": trend.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sales trend error: {str(e)}")


@app.get("/api/analytics/top-selling-products")
async def get_top_selling_products(limit: int = 5):
    """Return top selling products from the SQLite sales table."""
    try:
        if limit <= 0:
            raise HTTPException(status_code=400, detail="limit must be > 0")
        top_products = build_top_selling_products(top_n=limit)
        return {"products": top_products.to_dict(orient="records")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Top selling products error: {str(e)}")


@app.get("/api/analytics/apriori-rules")
async def get_market_basket_rules(
    min_support: float = 0.02,
    min_confidence: float = 0.25,
    min_lift: float = 1.0,
    top_n: int = 20,
):
    """Return Apriori association rules for market basket analysis."""
    try:
        if not (0 < min_support <= 1):
            raise HTTPException(status_code=400, detail="min_support must be between 0 and 1")
        if not (0 < min_confidence <= 1):
            raise HTTPException(status_code=400, detail="min_confidence must be between 0 and 1")
        if min_lift <= 0:
            raise HTTPException(status_code=400, detail="min_lift must be > 0")
        if top_n <= 0:
            raise HTTPException(status_code=400, detail="top_n must be > 0")

        return get_apriori_rules(
            min_support=min_support,
            min_confidence=min_confidence,
            min_lift=min_lift,
            top_n=top_n,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Apriori analysis error: {str(e)}")

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


@app.get("/api/customers/summary")
async def get_customer_summary():
    """Return customer master data, RFM metrics, and clustering summaries."""
    try:
        payload = customer_summary_payload()
        return {
            "customer_count": payload["customer_count"],
            "active_customers": payload["active_customers"],
            "total_spent": payload["total_spent"],
            "average_order_value": payload["average_order_value"],
            "segment_counts": payload["segment_counts"].to_dict(orient="records"),
            "kmeans_stats": payload["kmeans_stats"].to_dict(orient="records"),
            "top_customers": payload["top_customers"].to_dict(orient="records"),
            "category_counts": payload["category_counts"].to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Customer analytics error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
