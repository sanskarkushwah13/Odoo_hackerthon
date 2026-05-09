"""
Sample ERP Dataset Generator
Generates realistic business data for the AI Business Decision Copilot
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

# ─── Configuration ───────────────────────────────────────────────────────────
PRODUCTS = [
    ("Laptop Pro X1",    "Electronics",  1200, 80),
    ("Wireless Mouse",   "Electronics",    45, 500),
    ("Office Chair",     "Furniture",     350, 120),
    ("Standing Desk",    "Furniture",     600,  60),
    ("USB-C Hub",        "Electronics",    55, 400),
    ("Monitor 27inch",   "Electronics",   450, 100),
    ("Keyboard Mech",    "Electronics",    95, 300),
    ("Webcam HD",        "Electronics",    80, 250),
    ("Notebook A4",      "Stationery",      5, 2000),
    ("Pen Set",          "Stationery",     12, 1500),
    ("Desk Lamp",        "Furniture",      60, 200),
    ("Cable Manager",    "Accessories",    20, 600),
]

REGIONS = ["North", "South", "East", "West", "Central"]
CUSTOMER_IDS = [f"CUST_{i:04d}" for i in range(1, 201)]

def generate_erp_data(days: int = 365) -> pd.DataFrame:
    """Generate synthetic ERP transaction data."""
    records = []
    start_date = datetime(2024, 1, 1)

    for day_offset in range(days):
        date = start_date + timedelta(days=day_offset)
        month = date.month

        # Simulate seasonal patterns
        seasonal_factor = 1.0
        if month in [11, 12]:       # Q4 holiday boost
            seasonal_factor = 1.6
        elif month in [6, 7, 8]:    # Summer dip for office products
            seasonal_factor = 0.85
        elif month in [1, 2]:       # New-year slowdown
            seasonal_factor = 0.75

        # Daily transaction count
        n_transactions = int(np.random.poisson(15) * seasonal_factor)

        for _ in range(n_transactions):
            product_name, category, base_price, base_stock = random.choice(PRODUCTS)

            # Price variation ±15%
            price = base_price * np.random.uniform(0.85, 1.15)

            # Quantity: mostly small orders
            quantity = max(1, int(np.random.exponential(3)))

            # Occasional anomalies (spikes / drops)
            anomaly = random.random()
            if anomaly < 0.02:      # 2% chance of a spike
                quantity *= random.randint(5, 10)
            elif anomaly < 0.04:    # 2% chance of a near-zero day
                quantity = 1

            revenue = round(price * quantity, 2)

            # Inventory simulation
            inventory = max(0, int(base_stock - np.random.normal(base_stock * 0.3, base_stock * 0.15)))

            records.append({
                "date":         date.strftime("%Y-%m-%d"),
                "product_name": product_name,
                "category":     category,
                "customer_id":  random.choice(CUSTOMER_IDS),
                "region":       random.choice(REGIONS),
                "quantity":     quantity,
                "unit_price":   round(price, 2),
                "revenue":      revenue,
                "inventory":    inventory,
                "cost":         round(price * 0.6 * quantity, 2),
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["profit"] = df["revenue"] - df["cost"]
    df["profit_margin"] = (df["profit"] / df["revenue"] * 100).round(2)
    return df


if __name__ == "__main__":
    df = generate_erp_data(365)
    df.to_csv("erp_data.csv", index=False)
    print(f"✅ Generated {len(df):,} ERP records → erp_data.csv")
    print(df.head())
    print("\nColumns:", list(df.columns))
    print("Date range:", df["date"].min(), "→", df["date"].max())
