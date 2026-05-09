"""
Data Loader Utility
Handles CSV ingestion, validation, and caching of ERP data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import io
from typing import Optional, Tuple

REQUIRED_COLUMNS = {
    "date", "product_name", "revenue", "quantity", "inventory"
}

OPTIONAL_COLUMNS = {
    "category", "customer_id", "region", "unit_price", "cost", "profit", "profit_margin"
}


def load_csv(path_or_bytes) -> Tuple[pd.DataFrame, str]:
    """
    Load ERP data from a file path or raw bytes.
    Returns (DataFrame, error_message). error_message is '' on success.
    """
    try:
        if isinstance(path_or_bytes, (str, Path)):
            df = pd.read_csv(path_or_bytes)
        else:
            df = pd.read_csv(io.BytesIO(path_or_bytes))
    except Exception as e:
        return pd.DataFrame(), f"Could not read CSV: {e}"

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Validate required columns
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return pd.DataFrame(), f"Missing required columns: {missing}"

    # Parse date
    try:
        df["date"] = pd.to_datetime(df["date"])
    except Exception:
        return pd.DataFrame(), "Column 'date' could not be parsed as dates."

    # Fill optional computed columns
    if "cost" not in df.columns:
        df["cost"] = df["revenue"] * 0.6
    if "profit" not in df.columns:
        df["profit"] = df["revenue"] - df["cost"]
    if "profit_margin" not in df.columns:
        df["profit_margin"] = (df["profit"] / df["revenue"].replace(0, np.nan) * 100).fillna(0).round(2)
    if "category" not in df.columns:
        df["category"] = "General"
    if "region" not in df.columns:
        df["region"] = "Unknown"
    if "customer_id" not in df.columns:
        df["customer_id"] = "UNKNOWN"
    if "unit_price" not in df.columns:
        df["unit_price"] = (df["revenue"] / df["quantity"].replace(0, np.nan)).fillna(0)

    # Basic type coercion
    numeric_cols = ["revenue", "quantity", "inventory", "cost", "profit", "profit_margin", "unit_price"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df.sort_values("date").reset_index(drop=True)
    return df, ""


def get_default_data() -> pd.DataFrame:
    """Load the bundled sample ERP dataset."""
    sample_path = Path(__file__).parent.parent.parent / "data" / "erp_data.csv"
    if sample_path.exists():
        df, err = load_csv(sample_path)
        if not err:
            return df
    # Last-resort: generate in-memory
    from data.generate_sample_data import generate_erp_data
    return generate_erp_data(180)
