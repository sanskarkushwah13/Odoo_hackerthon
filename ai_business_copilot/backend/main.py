"""
FastAPI Backend — AI Business Decision Copilot
================================================
RESTful API exposing analytics, forecasting, anomaly detection,
recommendations, and AI chat endpoints.

Run with:  uvicorn backend.main:app --reload --port 8000
Docs at:   http://localhost:8000/docs
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.data_loader import load_csv, get_default_data
from backend.services.analytics_service      import AnalyticsService
from backend.services.forecasting_service    import ForecastingService
from backend.services.anomaly_service        import AnomalyDetectionService
from backend.services.recommendation_service import RecommendationEngine
from backend.services.ai_chat_service        import AIChatService

# ── App setup ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Business Decision Copilot API",
    description="ERP Analytics · Forecasting · Anomaly Detection · AI Recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory state (replace with DB in production) ────────────────────
_current_df: pd.DataFrame = get_default_data()


def _get_services():
    df = _current_df
    analytics   = AnalyticsService(df)
    forecasting = ForecastingService(df)
    anomaly     = AnomalyDetectionService(df)
    recommender = RecommendationEngine(df)
    context     = analytics.get_data_summary()
    ai_chat     = AIChatService(data_context=context)
    return analytics, forecasting, anomaly, recommender, ai_chat, df


# ══════════════════════════════════════════════════════════════════════════
#  PYDANTIC SCHEMAS
# ══════════════════════════════════════════════════════════════════════════
class ChatRequest(BaseModel):
    question: str
    history: List[dict] = []

class ChatResponse(BaseModel):
    answer: str
    source: str
    suggestions: List[str] = []


# ══════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════

# ── Health ────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "AI Business Decision Copilot API", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
def health():
    global _current_df
    return {
        "status":  "healthy",
        "records": len(_current_df),
        "date_range": {
            "from": str(_current_df["date"].min().date()),
            "to":   str(_current_df["date"].max().date()),
        },
    }


# ── Data Upload ───────────────────────────────────────────────────────────
@app.post("/upload", tags=["Data"], summary="Upload ERP CSV file")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file to replace the current ERP dataset.
    Required columns: date, product_name, revenue, quantity, inventory.
    """
    global _current_df
    raw = await file.read()
    df, err = load_csv(raw)
    if err:
        raise HTTPException(status_code=400, detail=err)
    _current_df = df
    return {
        "message":   f"Successfully loaded {len(df):,} records",
        "columns":   list(df.columns),
        "date_range": {
            "from": str(df["date"].min().date()),
            "to":   str(df["date"].max().date()),
        },
    }


# ── Analytics ─────────────────────────────────────────────────────────────
@app.get("/analytics/kpi", tags=["Analytics"], summary="Get KPI summary metrics")
def get_kpi():
    """Returns top-level KPIs: revenue, profit, orders, customers, margins."""
    analytics, *_ = _get_services()
    return analytics.get_kpi_summary()


@app.get("/analytics/monthly-revenue", tags=["Analytics"])
def get_monthly_revenue():
    analytics, *_ = _get_services()
    df = analytics.get_monthly_revenue()
    return df.to_dict(orient="records")


@app.get("/analytics/daily-revenue", tags=["Analytics"])
def get_daily_revenue(days: int = Query(90, ge=7, le=365)):
    analytics, *_ = _get_services()
    df = analytics.get_daily_revenue(days)
    df["date"] = df["date"].astype(str)
    return df.to_dict(orient="records")


@app.get("/analytics/top-products", tags=["Analytics"])
def get_top_products(n: int = Query(10, ge=1, le=50)):
    analytics, *_ = _get_services()
    df = analytics.get_top_products(n)
    return df.to_dict(orient="records")


@app.get("/analytics/revenue-by-region", tags=["Analytics"])
def get_revenue_by_region():
    analytics, *_ = _get_services()
    return analytics.get_revenue_by_region().to_dict(orient="records")


@app.get("/analytics/revenue-by-category", tags=["Analytics"])
def get_revenue_by_category():
    analytics, *_ = _get_services()
    return analytics.get_revenue_by_category().to_dict(orient="records")


@app.get("/analytics/customer-segments", tags=["Analytics"])
def get_customer_segments():
    analytics, *_ = _get_services()
    df = analytics.get_customer_segments()
    df["last_purchase"] = df["last_purchase"].astype(str)
    return df.head(100).to_dict(orient="records")


@app.get("/analytics/inventory-status", tags=["Analytics"])
def get_inventory_status():
    analytics, *_ = _get_services()
    df = analytics.get_inventory_status()
    df["risk"] = df["risk"].astype(str)
    return df.to_dict(orient="records")


# ── Forecasting ───────────────────────────────────────────────────────────
@app.get("/forecast/revenue", tags=["Forecasting"])
def forecast_revenue(
    periods: int = Query(30, ge=7, le=90),
    product: Optional[str] = Query(None),
):
    """Forecast daily revenue using Prophet or moving-average fallback."""
    _, forecasting, *_ = _get_services()
    result = forecasting.forecast_revenue(periods=periods, product_name=product)
    return result


@app.get("/forecast/demand", tags=["Forecasting"])
def forecast_demand(periods: int = Query(30, ge=7, le=90)):
    """Forecast demand (units) per product."""
    _, forecasting, *_ = _get_services()
    return forecasting.forecast_demand(periods=periods)


@app.get("/forecast/inventory-needs", tags=["Forecasting"])
def forecast_inventory_needs(safety_days: int = Query(14, ge=0, le=60)):
    _, forecasting, *_ = _get_services()
    df = forecasting.forecast_inventory_needs(safety_stock_days=safety_days)
    return df.to_dict(orient="records")


# ── Anomaly Detection ─────────────────────────────────────────────────────
@app.get("/anomalies/alerts", tags=["Anomaly Detection"])
def get_all_alerts():
    """Unified alert summary for the dashboard."""
    _, _, anomaly, *_ = _get_services()
    return anomaly.get_all_alerts()


@app.get("/anomalies/revenue", tags=["Anomaly Detection"])
def get_revenue_anomalies():
    _, _, anomaly, *_ = _get_services()
    df = anomaly.detect_revenue_anomalies()
    if df.empty:
        return []
    df["date"] = df["date"].astype(str)
    df["severity"] = df["severity"].astype(str)
    return df.to_dict(orient="records")


@app.get("/anomalies/products", tags=["Anomaly Detection"])
def get_product_anomalies():
    _, _, anomaly, *_ = _get_services()
    return anomaly.detect_product_anomalies().to_dict(orient="records")


@app.get("/anomalies/inventory", tags=["Anomaly Detection"])
def get_inventory_anomalies():
    _, _, anomaly, *_ = _get_services()
    df = anomaly.detect_inventory_anomalies()
    df["issue"]   = df["issue"].astype(str)
    return df.to_dict(orient="records")


# ── Recommendations ───────────────────────────────────────────────────────
@app.get("/recommendations/all", tags=["Recommendations"])
def get_all_recommendations():
    _, _, _, recommender, *_ = _get_services()
    return recommender.get_all_recommendations()


@app.get("/recommendations/restock", tags=["Recommendations"])
def get_restock_recommendations():
    _, _, _, recommender, *_ = _get_services()
    return recommender.get_restock_recommendations()


@app.get("/recommendations/pricing", tags=["Recommendations"])
def get_pricing_recommendations():
    _, _, _, recommender, *_ = _get_services()
    return recommender.get_pricing_recommendations()


@app.get("/recommendations/retention", tags=["Recommendations"])
def get_retention_recommendations():
    _, _, _, recommender, *_ = _get_services()
    return recommender.get_customer_retention_recommendations()


# ── AI Chat ───────────────────────────────────────────────────────────────
@app.post("/chat", tags=["AI Chat"], response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Ask a business question to the AI advisor.
    Optionally pass conversation history for multi-turn context.
    """
    _, _, _, _, ai_chat, _ = _get_services()
    result = ai_chat.ask(question=request.question, history=request.history)
    return ChatResponse(**result)


# ── Run directly ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
