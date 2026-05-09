from src.utils import load_or_generate_data

def get_erp_data():
    """Simulate ERP data layer."""
    df = load_or_generate_data()
    # You can extend this to connect to real ERP (PostgreSQL, Odoo, etc.)
    return df