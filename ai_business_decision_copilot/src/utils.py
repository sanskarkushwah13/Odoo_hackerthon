import pandas as pd
import numpy as np

def load_or_generate_data():
    """Load data from CSV, or generate if not exists."""
    try:
        df = pd.read_csv('data/sales_data.csv', parse_dates=['date'])
        print("Loaded existing data.")
    except FileNotFoundError:
        from data.generate_sample_data import generate_sales_data
        df = generate_sales_data()
    return df

def style_metric_card(value, delta=None):
    """Return formatted metric string."""
    if delta:
        return f"{value:,.0f} (Δ {delta:+.1f}%)"
    return f"{value:,.0f}"