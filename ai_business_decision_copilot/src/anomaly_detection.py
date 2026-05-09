# Anomaly detection module
import numpy as np
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    def __init__(self, df, column='total_sales', contamination=0.05):
        self.df = df
        self.column = column
        
        # Prepare data
        X = df[[column]].values
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.model.fit(X)
        self.preds = self.model.predict(X)
    
    def get_anomalies(self):
        """Return dataframe rows where anomaly is detected (-1)."""
        anomalies = self.df[self.preds == -1]
        return anomalies
    
    def get_recent_anomalies(self, n_days=7):
        """Get anomalies from last N days."""
        recent = self.df.tail(n_days)
        recent_preds = self.preds[-n_days:]
        return recent[recent_preds == -1]