"""
Anomaly Detection Service
Detects unusual patterns in sales, revenue, and inventory using
Isolation Forest (unsupervised) + statistical Z-score methods.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")


class AnomalyDetectionService:
    """Detects business anomalies across revenue, volume, and inventory."""

    CONTAMINATION = 0.05   # Expected anomaly rate

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df["date"] = pd.to_datetime(self.df["date"])

    # ─── Revenue Anomalies ────────────────────────────────────────────────────
    def detect_revenue_anomalies(self) -> pd.DataFrame:
        """
        Find days with abnormally high or low revenue using Isolation Forest.
        Returns a DataFrame of anomalous dates with severity labels.
        """
        daily = (
            self.df.groupby("date")
            .agg(revenue=("revenue", "sum"), orders=("revenue", "count"))
            .reset_index()
            .sort_values("date")
        )

        if len(daily) < 10:
            return pd.DataFrame()

        # Feature engineering
        daily["revenue_7d_ma"] = daily["revenue"].rolling(7, min_periods=1).mean()
        daily["revenue_pct_change"] = daily["revenue"].pct_change().fillna(0)
        daily["day_of_week"] = daily["date"].dt.dayofweek

        features = daily[["revenue", "orders", "revenue_7d_ma", "revenue_pct_change"]].fillna(0)
        scaler = StandardScaler()
        X = scaler.fit_transform(features)

        model = IsolationForest(
            contamination=self.CONTAMINATION,
            n_estimators=100,
            random_state=42,
        )
        daily["anomaly_score"] = model.fit_predict(X)
        daily["raw_score"]     = model.score_samples(X)

        anomalies = daily[daily["anomaly_score"] == -1].copy()
        anomalies["type"] = np.where(
            anomalies["revenue"] > anomalies["revenue_7d_ma"],
            "Revenue Spike",
            "Revenue Drop",
        )
        anomalies["severity"] = pd.cut(
            anomalies["raw_score"].abs(),
            bins=[0, 0.1, 0.2, float("inf")],
            labels=["Low", "Medium", "High"],
        )
        return anomalies[["date", "revenue", "revenue_7d_ma", "type", "severity", "raw_score"]].reset_index(drop=True)

    # ─── Product Anomalies ────────────────────────────────────────────────────
    def detect_product_anomalies(self) -> pd.DataFrame:
        """
        Z-score based anomaly detection per product monthly revenue.
        """
        monthly = (
            self.df.groupby(["product_name", self.df["date"].dt.to_period("M")])["revenue"]
            .sum()
            .reset_index()
        )
        monthly.columns = ["product_name", "month", "revenue"]

        results = []
        for product, group in monthly.groupby("product_name"):
            if len(group) < 3:
                continue
            mean = group["revenue"].mean()
            std  = group["revenue"].std(ddof=1) or 1
            group = group.copy()
            group["z_score"] = (group["revenue"] - mean) / std
            anomalous = group[group["z_score"].abs() > 2]
            for _, row in anomalous.iterrows():
                results.append({
                    "product":  product,
                    "month":    str(row["month"]),
                    "revenue":  round(row["revenue"], 2),
                    "z_score":  round(row["z_score"], 2),
                    "type":     "Spike" if row["z_score"] > 0 else "Drop",
                })

        return pd.DataFrame(results).sort_values("z_score", key=abs, ascending=False)

    # ─── Inventory Anomalies ──────────────────────────────────────────────────
    def detect_inventory_anomalies(self) -> pd.DataFrame:
        """
        Flag products with critically low or suspiciously high inventory.
        """
        inv = (
            self.df.groupby("product_name")
            .agg(
                avg_inventory=("inventory", "mean"),
                min_inventory=("inventory", "min"),
                avg_daily_qty=("quantity", "mean"),
            )
            .reset_index()
        )
        inv["days_of_stock"] = (inv["avg_inventory"] / inv["avg_daily_qty"].clip(lower=0.1)).round(1)

        # Z-score on days_of_stock
        mean_dos = inv["days_of_stock"].mean()
        std_dos  = inv["days_of_stock"].std(ddof=1) or 1
        inv["z_score"] = (inv["days_of_stock"] - mean_dos) / std_dos

        anomalies = inv[inv["z_score"].abs() > 1.5].copy()
        anomalies["issue"] = np.where(
            anomalies["days_of_stock"] < 14,
            "Stock-Out Risk",
            "Overstock Warning",
        )
        return anomalies[["product_name", "avg_inventory", "days_of_stock", "issue", "z_score"]].reset_index(drop=True)

    # ─── Aggregated Alert Summary ─────────────────────────────────────────────
    def get_all_alerts(self) -> Dict[str, Any]:
        """Return a unified alert summary for the dashboard."""
        rev_anomalies  = self.detect_revenue_anomalies()
        prod_anomalies = self.detect_product_anomalies()
        inv_anomalies  = self.detect_inventory_anomalies()

        alerts = []

        # Revenue alerts
        for _, row in rev_anomalies.iterrows():
            alerts.append({
                "category": "Revenue",
                "type":     row["type"],
                "severity": str(row.get("severity", "Medium")),
                "message":  f"{row['type']} on {str(row['date'])[:10]}: "
                            f"${row['revenue']:,.0f} vs avg ${row['revenue_7d_ma']:,.0f}",
            })

        # Product alerts (top 5)
        for _, row in prod_anomalies.head(5).iterrows():
            alerts.append({
                "category": "Product",
                "type":     f"Sales {row['type']}",
                "severity": "High" if abs(row["z_score"]) > 3 else "Medium",
                "message":  f"{row['product']} had unusual sales in {row['month']} "
                            f"(Z={row['z_score']:+.1f})",
            })

        # Inventory alerts
        for _, row in inv_anomalies.iterrows():
            severity = "High" if row["issue"] == "Stock-Out Risk" else "Low"
            alerts.append({
                "category": "Inventory",
                "type":     row["issue"],
                "severity": severity,
                "message":  f"{row['product_name']}: {row['days_of_stock']} days of stock remaining",
            })

        return {
            "total_alerts":         len(alerts),
            "high_severity":        sum(1 for a in alerts if a["severity"] == "High"),
            "alerts":               alerts[:20],   # cap at 20 for UI
            "revenue_anomaly_days": len(rev_anomalies),
            "inventory_at_risk":    int((inv_anomalies["issue"] == "Stock-Out Risk").sum()),
        }
