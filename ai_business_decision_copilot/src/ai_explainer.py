# AI explanation module
import os
from dotenv import load_dotenv
import openai

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
MOCK_MODE = os.getenv("MOCK_AI", "True").lower() == "true"

class AIExplainer:
    def __init__(self, analytics_engine, anomaly_detector, forecaster):
        self.analytics = analytics_engine
        self.anomaly = anomaly_detector
        self.forecaster = forecaster
    
    def generate_explanation(self, user_query):
        """Generate explanation for natural language query."""
        query_lower = user_query.lower()
        
        # Intent detection
        if "drop" in query_lower or "decrease" in query_lower:
            return self._explain_sales_drop()
        elif "forecast" in query_lower or "predict" in query_lower:
            return self._explain_forecast()
        elif "inventory" in query_lower:
            return self._explain_inventory()
        elif "recommend" in query_lower:
            return self._generate_recommendation_text()
        else:
            return self._general_analytics()
    
    def _explain_sales_drop(self):
        is_drop, pct = self.analytics.detect_sales_drop()
        if MOCK_MODE or not OPENAI_KEY:
            reason = "Sales dropped because inventory shortage affected top products and customer demand shifted."
            impact = f"Estimated lost revenue: ${abs(pct/100)*self.analytics.df['revenue'].tail(30).mean():.0f}"
            return f"**AI Analysis:** Sales decreased by {pct:.1f}% over last 30 days.\n- Root cause: {reason}\n- Impact: {impact}\n- Recommendation: Increase stock of high-margin items and launch a limited-time promotion."
        else:
            # Real OpenAI call (simplified)
            prompt = f"Sales dropped by {pct:.1f}% in last 30 days. Inventory correlation: {self.analytics.correlation_analysis():.2f}. Provide a short business explanation and 2 recommendations."
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
            return response.choices[0].message.content
    
    def _explain_forecast(self):
        forecast, upper, lower = self.forecaster.forecast(30)
        next_month = forecast.mean()
        return f"**Forecast:** Next month's expected sales = ${next_month:,.0f} (range ${lower.mean():,.0f} - ${upper.mean():,.0f}). Plan inventory accordingly."
    
    def _explain_inventory(self):
        days = self.analytics.inventory_health()
        if days < 15:
            return f"⚠️ **Critical inventory alert:** Only {days:.0f} days of stock remaining. Immediate restocking required for top products."
        else:
            return f"Inventory level is healthy – {days:.0f} days of supply."
    
    def _generate_recommendation_text(self):
        top = self.analytics.get_top_products(3)
        top_str = ", ".join([f"{p[0]} (${p[1]:,.0f})" for p in top])
        return f"**Top recommendations:**\n1. Increase stock for {top_str}\n2. Run a promotion on slow-moving categories\n3. Adjust pricing on Electronics (+5%) to boost margin."
    
    def _general_analytics(self):
        return "I can analyze sales trends, inventory health, and anomalies. Ask me: 'Why did sales drop?' or 'Forecast next month'."