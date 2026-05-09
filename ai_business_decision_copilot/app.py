import streamlit as st

# MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="AI Business Decision Copilot", layout="wide")

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings
warnings.filterwarnings('ignore')

# ------------------- DATA GENERATION -------------------
@st.cache_data
def load_or_generate_data():
    try:
        df = pd.read_csv('sales_data.csv', parse_dates=['date'])
    except FileNotFoundError:
        np.random.seed(42)
        days = 180
        dates = [datetime.today() - timedelta(days=i) for i in range(days, 0, -1)]
        base = 10000
        weekly = np.sin(np.linspace(0, 4*np.pi, days)) * 1500
        trend = np.linspace(0, 2000, days)
        noise = np.random.normal(0, 500, days)
        shortage = np.zeros(days)
        shortage[-30:] = -2500
        sales = base + weekly + trend + noise + shortage
        sales = np.maximum(sales, 1000)
        inventory = np.cumsum(np.random.choice([-200, 100, -50], days, p=[0.4,0.3,0.3])) + 8000
        inventory = np.clip(inventory, 500, 15000).astype(int)
        categories = ['Electronics', 'Clothing', 'Home', 'Toys']
        cat_sales = {}
        for cat in categories:
            cat_sales[cat] = sales * np.random.uniform(0.15, 0.35)
        df = pd.DataFrame({
            'date': dates,
            'total_sales': sales,
            'inventory_level': inventory,
            'revenue': sales * 45,
            'customers': np.random.poisson(sales / 80, days) + 20,
            'electronics_sales': cat_sales['Electronics'],
            'clothing_sales': cat_sales['Clothing'],
            'home_sales': cat_sales['Home'],
            'toys_sales': cat_sales['Toys']
        })
        df.to_csv('sales_data.csv', index=False)
    return df

df = load_or_generate_data()
df = df.sort_values('date').reset_index(drop=True)

# ------------------- ANALYTICS FUNCTIONS -------------------
def sales_change(period=30):
    recent = df['total_sales'].tail(period).mean()
    prev = df['total_sales'].tail(2*period).head(period).mean()
    return ((recent - prev) / prev) * 100 if prev != 0 else 0

def inventory_health():
    avg_inv = df['inventory_level'].tail(30).mean()
    avg_sales = df['total_sales'].tail(30).mean()
    return avg_inv / avg_sales if avg_sales > 0 else 999

def detect_anomalies():
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(df[['total_sales']])
    preds = model.predict(df[['total_sales']])
    return df[preds == -1]

def forecast_sales(steps=30):
    series = df.set_index('date')['total_sales']
    model = ExponentialSmoothing(series, seasonal_periods=7, trend='add', seasonal='add')
    fitted = model.fit()
    forecast = fitted.forecast(steps)
    resid_std = np.std(fitted.resid)
    upper = forecast + 1.96 * resid_std
    lower = forecast - 1.96 * resid_std
    return forecast, upper, lower

def get_top_categories(n=3):
    cat_cols = ['electronics_sales', 'clothing_sales', 'home_sales', 'toys_sales']
    latest = df[cat_cols].iloc[-1]
    top = latest.nlargest(n).index
    return [c.replace('_sales', '').capitalize() for c in top]

def generate_ai_insight(query):
    q = query.lower()
    if 'drop' in q or 'decrease' in q or 'why' in q:
        pct = sales_change()
        corr = df['total_sales'].corr(df['inventory_level'])
        if pct < -15:
            return f"📉 **Sales dropped by {pct:.1f}%** over last 30 days. Root cause: Inventory shortage (correlation {corr:.2f}). Recommendation: Restock top products and run a flash sale."
        else:
            return f"Sales are stable (change {pct:.1f}%). No major drop detected. Continue monitoring inventory."
    elif 'forecast' in q or 'predict' in q or 'future' in q:
        fcast, upper, lower = forecast_sales(30)
        return f"🔮 **Forecast for next month:** ${fcast.mean():,.0f} average (range ${lower.mean():,.0f} – ${upper.mean():,.0f}). Plan inventory accordingly."
    elif 'inventory' in q:
        days = inventory_health()
        if days < 20:
            return f"⚠️ **Critical inventory alert:** Only {days:.0f} days of stock left. Restock {', '.join(get_top_categories(2))}."
        else:
            return f"Inventory healthy – {days:.0f} days supply."
    elif 'recommend' in q:
        top = get_top_categories(2)
        return f"💡 **Recommendations:**\n- Increase stock for {', '.join(top)}\n- Run 10% discount on slow movers\n- Review supplier lead times"
    else:
        return "I can answer about sales drops, forecasts, inventory, or recommendations. Try: 'Why did sales drop?' or 'Forecast next month'."

# ------------------- UI -------------------
st.title("🧠 AI Business Decision Copilot")
st.caption("AI-powered ERP analytics | Proactive insights | Real-time alerts")

latest = df.iloc[-1]
prev_day = df.iloc[-2]
sales_daily_change = ((latest['total_sales'] - prev_day['total_sales']) / prev_day['total_sales']) * 100
inv_daily_change = ((latest['inventory_level'] - prev_day['inventory_level']) / prev_day['inventory_level']) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Today's Sales", f"${latest['total_sales']:,.0f}", f"{sales_daily_change:.1f}%")
col2.metric("📦 Inventory Level", f"{latest['inventory_level']:,.0f}", f"{inv_daily_change:.1f}%")
col3.metric("💰 MTD Revenue", f"${df['revenue'].tail(30).sum():,.0f}", "")
col4.metric("👥 Avg Customers (7d)", f"{df['customers'].tail(7).mean():.0f}", "")

drop_pct = sales_change()
if drop_pct < -15:
    st.error(f"⚠️ **Alert:** Sales dropped by {drop_pct:.1f}% over last 30 days.")
else:
    st.success(f"✅ Sales trend stable ({drop_pct:+.1f}% last 30 days).")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Sales & Anomalies", "🤖 AI Assistant", "📊 Forecast", "💡 Recommendations"])

with tab1:
    st.subheader("Sales Trend with Detected Anomalies")
    fig = px.line(df, x='date', y='total_sales', title="Daily Sales")
    anomalies = detect_anomalies()
    if not anomalies.empty:
        fig.add_scatter(x=anomalies['date'], y=anomalies['total_sales'], mode='markers',
                        marker=dict(color='red', size=10), name='Anomaly')
    st.plotly_chart(fig, use_container_width=True)
    
    colA, colB = st.columns(2)
    with colA:
        st.subheader("Inventory vs Sales Correlation")
        corr = df['total_sales'].corr(df['inventory_level'])
        st.metric("Correlation Coefficient", f"{corr:.2f}")
        # Removed trendline to avoid scipy import error
        fig2 = px.scatter(df.tail(90), x='inventory_level', y='total_sales',
                          title="Sales vs Inventory (last 90 days)")
        st.plotly_chart(fig2, use_container_width=True)
    with colB:
        st.subheader("Category Performance (Last 7 days)")
        cat_cols = ['electronics_sales', 'clothing_sales', 'home_sales', 'toys_sales']
        last_week = df[cat_cols].tail(7).mean()
        last_week.index = [c.replace('_sales', '').capitalize() for c in last_week.index]
        fig3 = px.bar(x=last_week.index, y=last_week.values, title="Avg Daily Sales by Category")
        st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.subheader("Ask the AI Copilot")
    user_query = st.text_input("Example: 'Why did sales drop last week?' or 'Forecast next month'")
    if st.button("Get Insight", type="primary"):
        with st.spinner("AI is analyzing your business data..."):
            answer = generate_ai_insight(user_query)
            st.markdown(f"### 🤖 AI Response\n{answer}")
    st.divider()
    st.subheader("Automated Business Insights")
    days_left = inventory_health()
    if days_left < 20:
        st.warning(f"🚨 **Inventory Alert:** Only {days_left:.0f} days of stock remaining. Restock soon.")
    else:
        st.info(f"📦 Inventory health: {days_left:.0f} days of supply.")
    st.subheader("Root Cause Analysis (Sales Drop)")
    if drop_pct < -15:
        corr_val = df['total_sales'].corr(df['inventory_level'])
        st.write(f"- Sales drop: **{drop_pct:.1f}%** over 30 days")
        st.write(f"- Correlation with inventory: **{corr_val:.2f}** (negative means shortage caused the drop)")
        st.success("✅ Recommendation: Expedite restocking and offer discounts on remaining inventory.")
    else:
        st.write("No significant sales drop detected. Key metrics are within normal range.")

with tab3:
    st.subheader("Demand Forecasting (30 days ahead)")
    forecast, upper, lower = forecast_sales(30)
    forecast_dates = pd.date_range(df['date'].max() + timedelta(days=1), periods=30)
    fcast_df = pd.DataFrame({'date': forecast_dates, 'forecast': forecast, 'upper': upper, 'lower': lower})
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=fcast_df['date'], y=fcast_df['forecast'], mode='lines', name='Forecast'))
    fig4.add_trace(go.Scatter(x=fcast_df['date'], y=fcast_df['upper'], mode='lines', name='Upper Bound', line=dict(dash='dot')))
    fig4.add_trace(go.Scatter(x=fcast_df['date'], y=fcast_df['lower'], mode='lines', name='Lower Bound', line=dict(dash='dot')))
    fig4.update_layout(title="Sales Forecast with Confidence Intervals", xaxis_title="Date", yaxis_title="Sales ($)")
    st.plotly_chart(fig4, use_container_width=True)
    st.metric("Expected Average Monthly Sales", f"${forecast.mean():,.0f}", delta=f"${forecast.mean() - df['total_sales'].tail(30).mean():,.0f}")

with tab4:
    st.subheader("Actionable Recommendations from AI")
    top_cats = get_top_categories(2)
    days_inv = inventory_health()
    if days_inv < 20:
        st.write(f"🚨 **Urgent restock** – only {days_inv:.0f} days of inventory left. Prioritize {top_cats[0]}.")
    else:
        st.write(f"✅ Inventory stable ({days_inv:.0f} days). Maintain just-in-time ordering.")
    if drop_pct < -15:
        st.write("📉 **Sales recovery plan**: Launch a 'limited time' discount on slow-moving categories and increase ad spend by 20%.")
    else:
        st.write("📈 **Growth opportunity**: Upsell complementary products to top categories.")
    st.write(f"⭐ **Focus on top performer**: {top_cats[0]} is your highest-selling category. Increase its shelf space and marketing.")
    st.write("💰 **Pricing optimization**: Electronics margins are high – test a 5% price increase.")

st.divider()
st.caption("AI Business Decision Copilot | Powered by Anomaly Detection, Forecasting & Rule-based AI | No API key required")