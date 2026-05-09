"""
Recommendation Engine
Generates actionable business recommendations:
- Restocking
- Pricing optimization
- Customer retention
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import warnings
warnings.filterwarnings("ignore")


class RecommendationEngine:
    """Rule-based + analytics-driven recommendation engine."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df["date"] = pd.to_datetime(self.df["date"])

    # ─── Restocking Recommendations ───────────────────────────────────────────
    def get_restock_recommendations(self) -> List[Dict[str, Any]]:
        """Identify products that need restocking based on velocity and stock."""
        inv = (
            self.df.groupby("product_name")
            .agg(
                current_stock=("inventory", "last"),
                avg_daily_qty=("quantity", "mean"),
                total_revenue=("revenue", "sum"),
            )
            .reset_index()
        )
        inv["days_of_stock"] = (inv["current_stock"] / inv["avg_daily_qty"].clip(lower=0.1)).round(1)

        recommendations = []
        for _, row in inv.iterrows():
            if row["days_of_stock"] < 30:
                urgency = "URGENT" if row["days_of_stock"] < 7 else ("HIGH" if row["days_of_stock"] < 14 else "MEDIUM")
                restock_qty = int(row["avg_daily_qty"] * 45)   # 45-day replenishment
                recommendations.append({
                    "product":          row["product_name"],
                    "current_stock":    int(row["current_stock"]),
                    "days_of_stock":    row["days_of_stock"],
                    "recommended_qty":  restock_qty,
                    "urgency":          urgency,
                    "monthly_revenue":  round(row["total_revenue"] / 12, 2),
                    "action":           f"Order {restock_qty} units immediately"
                                        if urgency == "URGENT" else f"Plan order of {restock_qty} units within 7 days",
                })

        return sorted(recommendations, key=lambda x: x["days_of_stock"])

    # ─── Pricing Recommendations ──────────────────────────────────────────────
    def get_pricing_recommendations(self) -> List[Dict[str, Any]]:
        """
        Suggest pricing adjustments based on margin analysis and demand elasticity proxies.
        """
        product_stats = (
            self.df.groupby("product_name")
            .agg(
                avg_price=("unit_price", "mean"),
                avg_margin=("profit_margin", "mean"),
                total_qty=("quantity", "sum"),
                revenue=("revenue", "sum"),
            )
            .reset_index()
        )

        recommendations = []
        for _, row in product_stats.iterrows():
            margin = row["avg_margin"]
            action = None

            if margin < 25:
                # Low margin — raise price or cut costs
                suggested_price = round(row["avg_price"] * 1.10, 2)
                action = {
                    "type":            "Price Increase",
                    "current_price":   round(row["avg_price"], 2),
                    "suggested_price": suggested_price,
                    "reason":          f"Low margin ({margin:.1f}%) — increase price by 10%",
                    "impact":          f"Estimated +{round(row['revenue'] * 0.10, 0):,.0f} revenue",
                }
            elif margin > 55 and row["total_qty"] < product_stats["total_qty"].median():
                # High margin but low volume — try a price drop to boost volume
                suggested_price = round(row["avg_price"] * 0.92, 2)
                action = {
                    "type":            "Price Reduction",
                    "current_price":   round(row["avg_price"], 2),
                    "suggested_price": suggested_price,
                    "reason":          f"High margin ({margin:.1f}%) but low volume — stimulate demand",
                    "impact":          "Expected +15-20% unit volume",
                }

            if action:
                recommendations.append({"product": row["product_name"], **action})

        return recommendations[:10]

    # ─── Customer Retention Recommendations ───────────────────────────────────
    def get_customer_retention_recommendations(self) -> List[Dict[str, Any]]:
        """
        Identify at-risk customers and recommend retention actions.
        """
        max_date = self.df["date"].max()
        customer_stats = (
            self.df.groupby("customer_id")
            .agg(
                last_purchase=("date", "max"),
                total_orders=("revenue", "count"),
                total_spend=("revenue", "sum"),
                avg_order=("revenue", "mean"),
            )
            .reset_index()
        )
        customer_stats["days_since_purchase"] = (
            max_date - customer_stats["last_purchase"]
        ).dt.days

        recommendations = []

        # Champions becoming inactive
        at_risk = customer_stats[
            (customer_stats["days_since_purchase"] > 45) &
            (customer_stats["total_spend"] > customer_stats["total_spend"].quantile(0.75))
        ]
        for _, row in at_risk.head(5).iterrows():
            recommendations.append({
                "customer_id":         row["customer_id"],
                "segment":             "High-Value At-Risk",
                "days_inactive":       int(row["days_since_purchase"]),
                "lifetime_value":      round(row["total_spend"], 2),
                "recommended_action":  "Send personalized win-back offer with 15% discount",
                "priority":            "HIGH",
            })

        # One-time buyers who could be converted
        one_time = customer_stats[
            (customer_stats["total_orders"] == 1) &
            (customer_stats["days_since_purchase"] < 30)
        ]
        for _, row in one_time.head(5).iterrows():
            recommendations.append({
                "customer_id":         row["customer_id"],
                "segment":             "New Customer",
                "days_inactive":       int(row["days_since_purchase"]),
                "lifetime_value":      round(row["total_spend"], 2),
                "recommended_action":  "Send follow-up email with loyalty program invitation",
                "priority":            "MEDIUM",
            })

        return recommendations

    # ─── Unified Summary ──────────────────────────────────────────────────────
    def get_all_recommendations(self) -> Dict[str, Any]:
        restock    = self.get_restock_recommendations()
        pricing    = self.get_pricing_recommendations()
        retention  = self.get_customer_retention_recommendations()

        return {
            "restock":          restock,
            "pricing":          pricing,
            "customer_retention": retention,
            "summary": {
                "urgent_restocks":    sum(1 for r in restock if r["urgency"] == "URGENT"),
                "pricing_actions":    len(pricing),
                "retention_actions":  len(retention),
            },
        }
