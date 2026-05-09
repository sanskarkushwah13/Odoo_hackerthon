"""
Analytics Service
Handles KPI calculations, trend analysis, and business intelligence queries.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings("ignore")


class AnalyticsService:
    """Core analytics engine for ERP data."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df["date"] = pd.to_datetime(self.df["date"])
        self.df["month"] = self.df["date"].dt.to_period("M")
        self.df["week"]  = self.df["date"].dt.to_period("W")

    # ─── KPI Summary ─────────────────────────────────────────────────────────
    def get_kpi_summary(self) -> Dict[str, Any]:
        """Return top-level KPI metrics."""
        total_revenue  = self.df["revenue"].sum()
        total_profit   = self.df["profit"].sum()
        total_orders   = len(self.df)
        unique_customers = self.df["customer_id"].nunique()
        avg_order_value  = self.df["revenue"].mean()
        avg_margin       = self.df["profit_margin"].mean()

        # Month-over-month change (last 2 complete months)
        monthly = self.df.groupby("month")["revenue"].sum().sort_index()
        mom_change = 0.0
        if len(monthly) >= 2:
            mom_change = ((monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2] * 100)

        return {
            "total_revenue":      round(total_revenue, 2),
            "total_profit":       round(total_profit, 2),
            "total_orders":       total_orders,
            "unique_customers":   unique_customers,
            "avg_order_value":    round(avg_order_value, 2),
            "avg_profit_margin":  round(avg_margin, 2),
            "mom_revenue_change": round(mom_change, 2),
        }

    # ─── Sales Trends ─────────────────────────────────────────────────────────
    def get_monthly_revenue(self) -> pd.DataFrame:
        monthly = (
            self.df.groupby("month")
            .agg(revenue=("revenue", "sum"), profit=("profit", "sum"), orders=("revenue", "count"))
            .reset_index()
        )
        monthly["month"] = monthly["month"].astype(str)
        return monthly

    def get_daily_revenue(self, last_n_days: int = 90) -> pd.DataFrame:
        cutoff = self.df["date"].max() - pd.Timedelta(days=last_n_days)
        daily = (
            self.df[self.df["date"] >= cutoff]
            .groupby("date")
            .agg(revenue=("revenue", "sum"), orders=("revenue", "count"))
            .reset_index()
        )
        return daily

    def get_revenue_by_region(self) -> pd.DataFrame:
        return (
            self.df.groupby("region")
            .agg(revenue=("revenue", "sum"), profit=("profit", "sum"))
            .reset_index()
            .sort_values("revenue", ascending=False)
        )

    def get_revenue_by_category(self) -> pd.DataFrame:
        return (
            self.df.groupby("category")
            .agg(revenue=("revenue", "sum"), profit=("profit", "sum"), orders=("revenue", "count"))
            .reset_index()
            .sort_values("revenue", ascending=False)
        )

    # ─── Product Analytics ────────────────────────────────────────────────────
    def get_top_products(self, n: int = 10) -> pd.DataFrame:
        return (
            self.df.groupby("product_name")
            .agg(
                revenue=("revenue", "sum"),
                profit=("profit", "sum"),
                quantity=("quantity", "sum"),
                orders=("revenue", "count"),
                avg_price=("unit_price", "mean"),
            )
            .reset_index()
            .sort_values("revenue", ascending=False)
            .head(n)
        )

    def get_product_trend(self, product_name: str) -> pd.DataFrame:
        """Monthly trend for a specific product."""
        return (
            self.df[self.df["product_name"] == product_name]
            .groupby("month")
            .agg(revenue=("revenue", "sum"), quantity=("quantity", "sum"))
            .reset_index()
            .assign(month=lambda x: x["month"].astype(str))
        )

    # ─── Inventory Analytics ──────────────────────────────────────────────────
    def get_inventory_status(self) -> pd.DataFrame:
        """Current inventory levels and stock-out risk."""
        inv = (
            self.df.groupby("product_name")
            .agg(
                avg_inventory=("inventory", "mean"),
                min_inventory=("inventory", "min"),
                avg_daily_sales=("quantity", "mean"),
            )
            .reset_index()
        )
        inv["days_of_stock"] = (inv["avg_inventory"] / inv["avg_daily_sales"].clip(lower=0.1)).round(1)
        inv["risk"] = pd.cut(
            inv["days_of_stock"],
            bins=[0, 7, 30, float("inf")],
            labels=["Critical", "Low", "Healthy"],
        )
        return inv.sort_values("days_of_stock")

    # ─── Customer Analytics ───────────────────────────────────────────────────
    def get_customer_segments(self) -> pd.DataFrame:
        """RFM-based customer segmentation."""
        max_date = self.df["date"].max()
        rfm = (
            self.df.groupby("customer_id")
            .agg(
                recency=("date", lambda x: (max_date - x.max()).days),
                frequency=("revenue", "count"),
                monetary=("revenue", "sum"),
            )
            .reset_index()
        )
        # Score each dimension 1-3
        for col in ["recency", "frequency", "monetary"]:
            ascending = col == "recency"          # lower recency = better
            rfm[f"{col}_score"] = pd.qcut(
                rfm[col], q=3, labels=[3, 2, 1] if ascending else [1, 2, 3]
            ).astype(int)

        rfm["rfm_score"] = rfm["recency_score"] + rfm["frequency_score"] + rfm["monetary_score"]
        rfm["segment"] = pd.cut(
            rfm["rfm_score"],
            bins=[0, 4, 6, 9],
            labels=["At-Risk", "Loyal", "Champions"],
        )
        return rfm

    # ─── Utility ──────────────────────────────────────────────────────────────
    def get_data_summary(self) -> str:
        """Return a text summary of the dataset for AI context."""
        kpi   = self.get_kpi_summary()
        top_p = self.get_top_products(3)["product_name"].tolist()
        top_r = self.get_revenue_by_region().iloc[0]["region"]

        return (
            f"ERP dataset: {len(self.df):,} transactions | "
            f"Total Revenue ${kpi['total_revenue']:,.0f} | "
            f"Avg Profit Margin {kpi['avg_profit_margin']:.1f}% | "
            f"MoM Revenue Change {kpi['mom_revenue_change']:+.1f}% | "
            f"Top Products: {', '.join(top_p)} | "
            f"Top Region: {top_r}"
        )
