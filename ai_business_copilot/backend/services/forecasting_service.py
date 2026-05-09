"""
Forecasting Service
Time-series forecasting for sales, revenue, and inventory using Prophet.
Falls back to a simple moving-average model if Prophet is unavailable.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import warnings
warnings.filterwarnings("ignore")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


class ForecastingService:
    """Sales and demand forecasting engine."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df["date"] = pd.to_datetime(self.df["date"])

    # ─── Internal helpers ─────────────────────────────────────────────────────
    def _daily_series(self, product_name: Optional[str] = None, metric: str = "revenue") -> pd.DataFrame:
        """Aggregate to daily ds/y format expected by Prophet."""
        subset = self.df if product_name is None else self.df[self.df["product_name"] == product_name]
        daily = subset.groupby("date")[metric].sum().reset_index()
        daily.columns = ["ds", "y"]
        return daily.sort_values("ds")

    def _fallback_forecast(self, series: pd.DataFrame, periods: int) -> pd.DataFrame:
        """Simple 30-day rolling-average fallback when Prophet is absent."""
        window = min(30, len(series))
        avg = series["y"].tail(window).mean()
        std = series["y"].tail(window).std(ddof=0) or avg * 0.1
        last_date = series["ds"].max()
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods)
        noise = np.random.normal(0, std * 0.2, size=periods)
        return pd.DataFrame({
            "ds":    future_dates,
            "yhat":  avg + noise,
            "yhat_lower": avg - std,
            "yhat_upper": avg + std,
        })

    # ─── Revenue Forecast ─────────────────────────────────────────────────────
    def forecast_revenue(self, periods: int = 30, product_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Forecast daily revenue for the next `periods` days.
        Returns historical + forecast DataFrames.
        """
        series = self._daily_series(product_name, metric="revenue")

        if PROPHET_AVAILABLE and len(series) >= 30:
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05,
            )
            model.fit(series)
            future   = model.make_future_dataframe(periods=periods)
            forecast = model.predict(future)
            forecast_only = forecast.tail(periods)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        else:
            forecast_only = self._fallback_forecast(series, periods)

        # Summary stats
        predicted_total = forecast_only["yhat"].clip(lower=0).sum()
        last_period     = series["y"].tail(periods).sum()
        growth_pct      = ((predicted_total - last_period) / max(last_period, 1)) * 100

        return {
            "historical":       series.tail(90).to_dict(orient="records"),
            "forecast":         forecast_only.to_dict(orient="records"),
            "predicted_total":  round(predicted_total, 2),
            "growth_pct":       round(growth_pct, 2),
            "periods":          periods,
            "product":          product_name or "All Products",
            "method":           "Prophet" if (PROPHET_AVAILABLE and len(series) >= 30) else "Moving Average",
        }

    # ─── Demand Forecast ──────────────────────────────────────────────────────
    def forecast_demand(self, periods: int = 30) -> Dict[str, Any]:
        """Forecast quantity demand per product for next `periods` days."""
        results = {}
        products = self.df["product_name"].unique()

        for product in products:
            series = self._daily_series(product, metric="quantity")
            if len(series) < 7:
                continue

            if PROPHET_AVAILABLE and len(series) >= 30:
                model = Prophet(
                    daily_seasonality=False,
                    weekly_seasonality=True,
                    yearly_seasonality=len(series) >= 365,
                    changepoint_prior_scale=0.1,
                )
                model.fit(series)
                future   = model.make_future_dataframe(periods=periods)
                forecast = model.predict(future)
                predicted = max(0, forecast["yhat"].tail(periods).sum())
            else:
                window    = min(30, len(series))
                predicted = series["y"].tail(window).mean() * periods

            results[product] = {
                "predicted_units": round(predicted, 1),
                "daily_avg":       round(predicted / periods, 2),
            }

        return {
            "demand_by_product": results,
            "periods":           periods,
            "method":            "Prophet" if PROPHET_AVAILABLE else "Moving Average",
        }

    # ─── Inventory Forecast ───────────────────────────────────────────────────
    def forecast_inventory_needs(self, safety_stock_days: int = 14) -> pd.DataFrame:
        """
        Estimate restock quantities needed for the next 30 days.
        Returns a DataFrame with columns: product, current_stock, predicted_demand,
        restock_needed, restock_qty.
        """
        demand_data   = self.forecast_demand(periods=30)["demand_by_product"]
        current_stock = (
            self.df.groupby("product_name")["inventory"].last().to_dict()
        )
        rows = []
        for product, demand_info in demand_data.items():
            stock      = current_stock.get(product, 0)
            needed     = demand_info["predicted_units"]
            safety     = demand_info["daily_avg"] * safety_stock_days
            restock    = max(0, needed + safety - stock)

            rows.append({
                "product":          product,
                "current_stock":    round(stock, 0),
                "predicted_demand": round(needed, 0),
                "safety_stock":     round(safety, 0),
                "restock_qty":      round(restock, 0),
                "restock_needed":   restock > 0,
            })

        return pd.DataFrame(rows).sort_values("restock_qty", ascending=False)
