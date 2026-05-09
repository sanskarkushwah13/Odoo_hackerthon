# Recommendation engine module
class RecommendationEngine:
    def __init__(self, analytics):
        self.analytics = analytics
    
    def get_recommendations(self):
        """Return list of actionable recommendations."""
        recs = []
        # Inventory
        days = self.analytics.inventory_health()
        if days < 20:
            recs.append(f"🚨 Restock urgently – only {days:.0f} days of inventory left.")
        elif days > 90:
            recs.append("📉 Reduce inventory to free up cash – slow turnover detected.")
        
        # Sales drop
        is_drop, pct = self.analytics.detect_sales_drop()
        if is_drop:
            recs.append(f"📉 Sales dropped {pct:.1f}% – consider promotional campaign and check supply chain.")
        
        # Top product suggestions
        top = self.analytics.get_top_products(2)
        for prod, val in top:
            recs.append(f"⭐ {prod} is a top performer – ensure adequate stock and highlight in marketing.")
        
        if not recs:
            recs.append("✅ All KPIs are stable. Focus on maintaining current strategy.")
        
        return recs