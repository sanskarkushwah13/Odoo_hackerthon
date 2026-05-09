# Forecasting module
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

class DemandForecaster:
    def __init__(self, df, column='total_sales'):
        self.df = df.copy()
        self.column = column
        self.model = None
    
    def fit_ets(self):
        """Fit exponential smoothing model."""
        series = self.df.set_index('date')[self.column]
        self.model = ExponentialSmoothing(series, seasonal_periods=7, trend='add', seasonal='add')
        self.fitted = self.model.fit()
    
    def forecast(self, steps=30):
        """Return forecasted values and confidence intervals."""
        if self.model is None:
            self.fit_ets()
        forecast = self.fitted.forecast(steps)
        # crude confidence intervals: ±1.96 * residual std
        resid_std = np.std(self.fitted.resid)
        upper = forecast + 1.96 * resid_std
        lower = forecast - 1.96 * resid_std
        return forecast, upper, lower