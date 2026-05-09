import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sales_data(days=180, seed=42):
    np.random.seed(seed)
    dates = [datetime.today() - timedelta(days=i) for i in range(days, 0, -1)]
    
    # Base sales with weekly seasonality and a recent dip
    base_sales = 10000
    weekly_pattern = np.sin(np.linspace(0, 4*np.pi, days)) * 1500
    trend = np.linspace(0, 2000, days)  # gradual growth
    noise = np.random.normal(0, 500, days)
    
    # Simulate inventory shortage effect last 30 days
    shortage_effect = np.zeros(days)
    shortage_effect[-30:] = -2000
    
    sales = base_sales + weekly_pattern + trend + noise + shortage_effect
    sales = np.maximum(sales, 1000)  # floor
    
    # Inventory levels (decrease when sales high, restock randomly)
    inventory = 5000 + np.random.randint(-200, 300, days)
    inventory = np.cumsum(np.random.choice([-200, 100, -50], days, p=[0.4,0.3,0.3])) + 8000
    inventory = np.clip(inventory, 500, 15000).astype(int)
    
    # Product categories
    categories = ['Electronics', 'Clothing', 'Home', 'Toys']
    category_sales = {}
    for cat in categories:
        category_sales[cat] = np.random.choice([0.2, 0.3, 0.25, 0.25], 1)[0] * sales
        category_sales[cat] = np.maximum(category_sales[cat], 50)
    
    df = pd.DataFrame({
        'date': dates,
        'total_sales': sales,
        'inventory_level': inventory,
        'electronics_sales': category_sales['Electronics'],
        'clothing_sales': category_sales['Clothing'],
        'home_sales': category_sales['Home'],
        'toys_sales': category_sales['Toys'],
        'revenue': sales * 45,  # assume $45 avg price
        'customers': np.random.poisson(sales / 80, days) + 20
    })
    
    df.to_csv('data/sales_data.csv', index=False)
    print("Sample data saved to data/sales_data.csv")
    return df

if __name__ == "__main__":
    generate_sales_data()