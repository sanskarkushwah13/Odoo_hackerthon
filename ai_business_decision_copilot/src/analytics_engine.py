# Analytics engine module
import pandas as pd
import numpy as np

class AnalyticsEngine:
    def __init__(self, df):
        self.df = df.copy()
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df = self.df.sort_values('date')
    
    def compute_period_over_period(self, column='total_sales', lookback_days=30):
        """Calculate percentage change over the last N days."""
        recent = self.df.tail(lookback_days)[column].mean()
        previous = self.df.tail(2*lookback_days).head(lookback_days)[column].mean() if len(self.df) > 2*lookback_days else recent
        pct_change = ((recent - previous) / previous) * 100 if previous != 0 else 0
        return pct_change, recent, previous
    
    def detect_sales_drop(self, threshold=-15):
        """Return True if sales dropped more than threshold %."""
        pct, _, _ = self.compute_period_over_period()
        return pct < threshold, pct
    
    def get_top_products(self, n=3):
        """Return top selling categories."""
        sales_cols = [c for c in self.df.columns if 'sales' in c and c != 'total_sales']
        latest = self.df.iloc[-1]
        top = {col: latest[col] for col in sales_cols}
        sorted_top = sorted(top.items(), key=lambda x: x[1], reverse=True)[:n]
        return sorted_top
    
    def inventory_health(self):
        """Compute inventory turnover estimate."""
        avg_inventory = self.df['inventory_level'].tail(30).mean()
        avg_sales = self.df['total_sales'].tail(30).mean()
        days_to_deplete = avg_inventory / avg_sales if avg_sales > 0 else 999
        return days_to_deplete
    
    def correlation_analysis(self):
        """Correlate sales with inventory."""
        corr = self.df['total_sales'].corr(self.df['inventory_level'])
        return corr