"""
AI Business Decision Copilot — Streamlit Dashboard
======================================================
A production-grade ERP analytics platform with:
  • KPI cards            • Sales & revenue charts
  • Forecasting          • Anomaly detection alerts
  • Recommendation panel • AI chatbot assistant
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# ── local imports ──────────────────────────────────────────────────────────
from backend.utils.data_loader import load_csv, get_default_data
from backend.services.analytics_service    import AnalyticsService
from backend.services.forecasting_service  import ForecastingService
from backend.services.anomaly_service      import AnomalyDetectionService
from backend.services.recommendation_service import RecommendationEngine
from backend.services.ai_chat_service     import AIChatService

# ══════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG & THEME
# ══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Business Decision Copilot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Global background ── */
.stApp { background: #0d0f14; color: #e2e8f0; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #0d1117 100%);
    border-right: 1px solid #1f2937;
}

/* ── KPI cards ── */
.kpi-card {
    background: linear-gradient(135deg, #1a2235 0%, #111827 100%);
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    transition: transform .2s, box-shadow .2s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(99,179,237,.15); }
.kpi-label { color: #94a3b8; font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 6px; }
.kpi-value { color: #f1f5f9; font-size: 28px; font-weight: 700; font-family: 'Space Mono', monospace; }
.kpi-delta { font-size: 12px; margin-top: 4px; font-weight: 500; }
.delta-pos { color: #34d399; }
.delta-neg { color: #f87171; }

/* ── Section headers ── */
.section-header {
    display: flex; align-items: center; gap: 10px;
    font-size: 18px; font-weight: 700; color: #f1f5f9;
    margin: 28px 0 16px; padding-bottom: 10px;
    border-bottom: 1px solid #1f2937;
}

/* ── Alert cards ── */
.alert-high   { background:#2d1515; border-left:4px solid #ef4444; border-radius:8px; padding:12px 16px; margin:8px 0; }
.alert-medium { background:#2d2515; border-left:4px solid #f59e0b; border-radius:8px; padding:12px 16px; margin:8px 0; }
.alert-low    { background:#152d1f; border-left:4px solid #10b981; border-radius:8px; padding:12px 16px; margin:8px 0; }
.alert-msg    { color:#e2e8f0; font-size:14px; }
.alert-badge  { font-size:11px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }

/* ── Rec cards ── */
.rec-card {
    background:#111827; border:1px solid #1f2937; border-radius:10px;
    padding:16px; margin:8px 0;
}
.rec-title { color:#93c5fd; font-weight:600; font-size:14px; margin-bottom:6px; }
.rec-body  { color:#94a3b8; font-size:13px; line-height:1.6; }

/* ── Chat bubbles ── */
.chat-user {
    background: linear-gradient(135deg,#1e3a5f,#1a2f4e);
    border-radius:16px 16px 4px 16px; padding:12px 16px; margin:8px 0 8px auto;
    max-width:80%; float:right; clear:both; color:#e2e8f0; font-size:14px;
}
.chat-ai {
    background:#1a2235; border:1px solid #1f2937;
    border-radius:16px 16px 16px 4px; padding:14px 18px; margin:8px 0;
    max-width:85%; float:left; clear:both; color:#e2e8f0; font-size:14px; line-height:1.7;
}
.chat-source { font-size:11px; color:#4b5563; margin-top:4px; }
div[style*="clear:both"] { clear:both; }

/* ── Plotly chart override ── */
.js-plotly-plot .plotly .modebar { background:transparent !important; }

/* ── Upload area ── */
.upload-zone {
    border:2px dashed #374151; border-radius:12px; padding:30px;
    text-align:center; color:#6b7280;
}

/* ── Tab style ── */
.stTabs [data-baseweb="tab"] { color:#94a3b8; font-weight:500; }
.stTabs [aria-selected="true"] { color:#60a5fa !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════
CHART_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", size=12),
    xaxis=dict(gridcolor="#1f2937", linecolor="#374151"),
    yaxis=dict(gridcolor="#1f2937", linecolor="#374151"),
    margin=dict(t=40, b=40, l=20, r=20),
)
PALETTE = ["#60a5fa","#34d399","#f59e0b","#f87171","#a78bfa","#38bdf8","#fb923c","#4ade80"]

def apply_theme(fig):
    fig.update_layout(**CHART_THEME)
    return fig

def kpi_card(label, value, delta=None, prefix="", suffix=""):
    delta_html = ""
    if delta is not None:
        cls = "delta-pos" if delta >= 0 else "delta-neg"
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f'<div class="kpi-delta {cls}">{arrow} {abs(delta):.1f}%</div>'
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{prefix}{value}{suffix}</div>
        {delta_html}
    </div>"""

def section(icon, title):
    st.markdown(f'<div class="section-header">{icon} {title}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
#  DATA LOADING & CACHING
# ══════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_services(df: pd.DataFrame):
    analytics   = AnalyticsService(df)
    forecasting = ForecastingService(df)
    anomaly     = AnomalyDetectionService(df)
    recommender = RecommendationEngine(df)
    context     = analytics.get_data_summary()
    ai_chat     = AIChatService(data_context=context)
    return analytics, forecasting, anomaly, recommender, ai_chat

# ══════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:16px 0 8px">
        <div style="font-size:32px">🧠</div>
        <div style="font-size:18px;font-weight:700;color:#f1f5f9">AI Business</div>
        <div style="font-size:14px;color:#60a5fa;font-weight:600">Decision Copilot</div>
        <div style="font-size:11px;color:#4b5563;margin-top:4px">ERP Analytics Platform</div>
    </div>
    <hr style="border-color:#1f2937;margin:16px 0">
    """, unsafe_allow_html=True)

    st.markdown("**📂 Data Source**")
    use_sample = st.toggle("Use Sample ERP Data", value=True)

    df = None
    if not use_sample:
        uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        if uploaded:
            raw = uploaded.read()
            df, err = load_csv(raw)
            if err:
                st.error(f"❌ {err}")
                df = None
            else:
                st.success(f"✅ {len(df):,} rows loaded")

    if df is None:
        df = get_default_data()
        if not use_sample:
            st.info("Using sample data — upload a CSV above.")

    st.markdown("<hr style='border-color:#1f2937;margin:16px 0'>", unsafe_allow_html=True)

    # Filters
    st.markdown("**🔧 Filters**")
    all_regions  = ["All"] + sorted(df["region"].unique().tolist())
    all_cats     = ["All"] + sorted(df["category"].unique().tolist())
    sel_region   = st.selectbox("Region", all_regions)
    sel_category = st.selectbox("Category", all_cats)

    date_min = df["date"].min().date()
    date_max = df["date"].max().date()
    date_range = st.date_input("Date Range", value=(date_min, date_max),
                               min_value=date_min, max_value=date_max)

    # Apply filters
    fdf = df.copy()
    if sel_region   != "All": fdf = fdf[fdf["region"]   == sel_region]
    if sel_category != "All": fdf = fdf[fdf["category"] == sel_category]
    if len(date_range) == 2:
        fdf = fdf[(fdf["date"].dt.date >= date_range[0]) & (fdf["date"].dt.date <= date_range[1])]

    st.markdown("<hr style='border-color:#1f2937;margin:16px 0'>", unsafe_allow_html=True)
    st.markdown("**🤖 AI Settings**")
    st.caption("Set ANTHROPIC_API_KEY env var to enable Claude AI. Runs built-in engine otherwise.")

    st.markdown("<hr style='border-color:#1f2937;margin:16px 0'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:11px;color:#4b5563;text-align:center">
        Records: <b style="color:#6b7280">{len(fdf):,}</b> &nbsp;|&nbsp;
        Products: <b style="color:#6b7280">{fdf['product_name'].nunique()}</b><br>
        Date range: <b style="color:#6b7280">{fdf['date'].min().strftime('%b %Y')}</b> →
                    <b style="color:#6b7280">{fdf['date'].max().strftime('%b %Y')}</b>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
#  LOAD SERVICES
# ══════════════════════════════════════════════════════════════════════════
with st.spinner("🔄 Running analytics engine..."):
    analytics, forecasting, anomaly, recommender, ai_chat = load_services(fdf)

kpi          = analytics.get_kpi_summary()
alerts_data  = anomaly.get_all_alerts()

# ══════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <h1 style="font-size:28px;font-weight:800;color:#f1f5f9;margin:0">
        🧠 AI Business Decision Copilot
    </h1>
    <p style="color:#64748b;font-size:14px;margin:4px 0 0">
        ERP Analytics · Forecasting · Anomaly Detection · AI Recommendations
    </p>
    """, unsafe_allow_html=True)
with col_h2:
    alert_count = alerts_data["high_severity"]
    color = "#ef4444" if alert_count > 0 else "#34d399"
    st.markdown(f"""
    <div style="text-align:right;padding:12px 0">
        <span style="background:{color}22;border:1px solid {color};
              color:{color};border-radius:20px;padding:6px 14px;
              font-size:13px;font-weight:600">
            🔔 {alert_count} High-Priority Alert{'s' if alert_count != 1 else ''}
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border-color:#1f2937;margin:8px 0 20px'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
#  KPI CARDS
# ══════════════════════════════════════════════════════════════════════════
c1, c2, c3, c4, c5, c6 = st.columns(6)
cards = [
    (c1, "Total Revenue",       f"${kpi['total_revenue']:,.0f}",        "",      "",    kpi["mom_revenue_change"]),
    (c2, "Total Profit",        f"${kpi['total_profit']:,.0f}",          "",      "",    None),
    (c3, "Total Orders",        f"{kpi['total_orders']:,}",              "",      "",    None),
    (c4, "Unique Customers",    f"{kpi['unique_customers']:,}",          "",      "",    None),
    (c5, "Avg Order Value",     f"${kpi['avg_order_value']:,.2f}",       "",      "",    None),
    (c6, "Avg Profit Margin",   f"{kpi['avg_profit_margin']:.1f}%",      "",      "",    None),
]
for col, label, value, prefix, suffix, delta in cards:
    with col:
        st.markdown(kpi_card(label, value, delta), unsafe_allow_html=True)

st.markdown("<div style='margin:24px 0'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
#  MAIN TABS
# ══════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Sales Analytics",
    "🔮 Forecasting",
    "⚠️ Anomalies",
    "💡 Recommendations",
    "🤖 AI Assistant",
    "📦 Inventory",
])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 — Sales Analytics
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    col_a, col_b = st.columns([2, 1])

    # Monthly revenue chart
    with col_a:
        section("📈", "Monthly Revenue & Profit")
        monthly = analytics.get_monthly_revenue()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly["month"], y=monthly["revenue"],
                             name="Revenue", marker_color="#60a5fa", opacity=0.85))
        fig.add_trace(go.Bar(x=monthly["month"], y=monthly["profit"],
                             name="Profit",  marker_color="#34d399", opacity=0.85))
        fig.add_trace(go.Scatter(x=monthly["month"], y=monthly["orders"],
                                 name="Orders", yaxis="y2",
                                 line=dict(color="#f59e0b", width=2),
                                 mode="lines+markers", marker=dict(size=5)))
        fig.update_layout(
            **CHART_THEME,
            barmode="group", height=320,
            yaxis=dict(title="Revenue / Profit ($)", gridcolor="#1f2937"),
            yaxis2=dict(title="Orders", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"),
            legend=dict(orientation="h", y=1.05, bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Revenue by region
    with col_b:
        section("🗺️", "Revenue by Region")
        region_df = analytics.get_revenue_by_region()
        fig2 = px.pie(region_df, names="region", values="revenue",
                      color_discrete_sequence=PALETTE,
                      hole=0.55)
        fig2.update_traces(textposition="outside", textinfo="percent+label")
        fig2.update_layout(**CHART_THEME, height=320, showlegend=False,
                           annotations=[dict(text="Region", x=0.5, y=0.5,
                                             font_size=13, showarrow=False,
                                             font_color="#94a3b8")])
        st.plotly_chart(fig2, use_container_width=True)

    # Daily rolling revenue
    section("📉", "Daily Revenue (Last 90 Days)")
    daily = analytics.get_daily_revenue(90)
    daily["7d_ma"] = daily["revenue"].rolling(7, min_periods=1).mean()
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=daily["date"], y=daily["revenue"],
                              name="Daily Revenue",
                              fill="tozeroy", fillcolor="rgba(96,165,250,.1)",
                              line=dict(color="#60a5fa", width=1.5), mode="lines"))
    fig3.add_trace(go.Scatter(x=daily["date"], y=daily["7d_ma"],
                              name="7-Day MA",
                              line=dict(color="#f59e0b", width=2.5, dash="dot")))
    fig3.update_layout(**CHART_THEME, height=270,
                       legend=dict(orientation="h", y=1.05, bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig3, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        section("🏆", "Top Products by Revenue")
        top_p = analytics.get_top_products(8)
        fig4 = px.bar(top_p.sort_values("revenue"),
                      x="revenue", y="product_name", orientation="h",
                      color="profit", color_continuous_scale=["#f87171","#f59e0b","#34d399"],
                      text=top_p.sort_values("revenue")["revenue"].apply(lambda x: f"${x:,.0f}"))
        fig4.update_traces(textposition="outside")
        fig4.update_layout(**CHART_THEME, height=320, coloraxis_showscale=False,
                           yaxis_title="", xaxis_title="Revenue ($)")
        st.plotly_chart(fig4, use_container_width=True)

    with col_d:
        section("🗂️", "Revenue by Category")
        cat_df = analytics.get_revenue_by_category()
        fig5 = px.bar(cat_df, x="category", y=["revenue","profit"],
                      barmode="group", color_discrete_sequence=["#60a5fa","#34d399"])
        fig5.update_layout(**CHART_THEME, height=320,
                           legend=dict(orientation="h", y=1.05, bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 2 — Forecasting
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    section("🔮", "Revenue Forecasting")

    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f1:
        forecast_days    = st.slider("Forecast horizon (days)", 7, 90, 30)
    with col_f2:
        products_list    = ["All Products"] + sorted(fdf["product_name"].unique().tolist())
        selected_product = st.selectbox("Filter by product", products_list)
    with col_f3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        run_forecast = st.button("🔮 Run Forecast", use_container_width=True)

    product_param = None if selected_product == "All Products" else selected_product

    with st.spinner("⚙️ Training forecasting model..."):
        fc = forecasting.forecast_revenue(periods=forecast_days, product_name=product_param)

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Predicted Revenue", f"${fc['predicted_total']:,.0f}")
    m2.metric("Growth vs Prior Period", f"{fc['growth_pct']:+.1f}%")
    m3.metric("Model", fc["method"])

    # Forecast chart
    hist_df     = pd.DataFrame(fc["historical"])
    forecast_df = pd.DataFrame(fc["forecast"])
    hist_df["ds"]     = pd.to_datetime(hist_df["ds"])
    forecast_df["ds"] = pd.to_datetime(forecast_df["ds"])

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Scatter(
        x=hist_df["ds"], y=hist_df["y"],
        name="Historical", line=dict(color="#60a5fa", width=2), mode="lines"))
    fig_fc.add_trace(go.Scatter(
        x=forecast_df["ds"], y=forecast_df["yhat"].clip(lower=0),
        name="Forecast", line=dict(color="#f59e0b", width=2.5, dash="dash")))
    if "yhat_upper" in forecast_df.columns:
        fig_fc.add_trace(go.Scatter(
            x=pd.concat([forecast_df["ds"], forecast_df["ds"][::-1]]),
            y=pd.concat([forecast_df["yhat_upper"], forecast_df["yhat_lower"][::-1]]).clip(lower=0),
            fill="toself", fillcolor="rgba(245,158,11,.12)",
            line=dict(color="rgba(0,0,0,0)"), name="Confidence Band"))
    # Vertical divider
    if len(hist_df):
        split_date = hist_df["ds"].max()
        fig_fc.add_vline(x=split_date, line_dash="dot", line_color="#374151",
                         annotation_text="Forecast Start", annotation_font_color="#94a3b8")
    fig_fc.update_layout(**CHART_THEME, height=380,
                         legend=dict(orientation="h", y=1.05, bgcolor="rgba(0,0,0,0)"),
                         yaxis_title="Revenue ($)", xaxis_title="")
    st.plotly_chart(fig_fc, use_container_width=True)

    # Inventory restock forecast
    section("📦", "30-Day Inventory Restock Forecast")
    inv_fc = forecasting.forecast_inventory_needs()
    urgent = inv_fc[inv_fc["restock_needed"]]
    if not urgent.empty:
        fig_inv = px.bar(urgent.head(10), x="product", y="restock_qty",
                         color="restock_qty", color_continuous_scale=["#34d399","#f59e0b","#ef4444"],
                         text=urgent.head(10)["restock_qty"].astype(int))
        fig_inv.update_traces(textposition="outside")
        fig_inv.update_layout(**CHART_THEME, height=300, coloraxis_showscale=False,
                              xaxis_title="", yaxis_title="Units to Restock")
        st.plotly_chart(fig_inv, use_container_width=True)
    else:
        st.success("✅ All products have adequate projected stock for the next 30 days.")

# ─────────────────────────────────────────────────────────────────────────
# TAB 3 — Anomaly Detection
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    section("⚠️", "Business Anomaly Alerts")

    alerts = alerts_data["alerts"]
    if not alerts:
        st.success("✅ No anomalies detected in the current dataset.")
    else:
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Total Alerts",       alerts_data["total_alerts"])
        col_s2.metric("High Severity",      alerts_data["high_severity"])
        col_s3.metric("Inventory At Risk",  alerts_data["inventory_at_risk"])

        # Severity filter
        sev_filter = st.multiselect("Filter by Severity",
                                    ["High","Medium","Low"], default=["High","Medium","Low"])

        for a in alerts:
            if a["severity"] not in sev_filter:
                continue
            cls = {"High":"alert-high","Medium":"alert-medium","Low":"alert-low"}.get(a["severity"],"alert-low")
            badge_color = {"High":"#ef4444","Medium":"#f59e0b","Low":"#34d399"}.get(a["severity"],"#34d399")
            st.markdown(f"""
            <div class="{cls}">
                <span class="alert-badge" style="color:{badge_color}">
                    [{a['severity']}] {a['category']} · {a['type']}
                </span>
                <div class="alert-msg" style="margin-top:6px">{a['message']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Revenue anomaly chart
    section("📉", "Revenue Anomaly Timeline")
    rev_anom = anomaly.detect_revenue_anomalies()
    daily90  = analytics.get_daily_revenue(365)

    fig_anom = go.Figure()
    fig_anom.add_trace(go.Scatter(
        x=daily90["date"], y=daily90["revenue"],
        name="Revenue", line=dict(color="#60a5fa", width=1.5),
        fill="tozeroy", fillcolor="rgba(96,165,250,.08)"))
    if not rev_anom.empty:
        spikes = rev_anom[rev_anom["type"] == "Revenue Spike"]
        drops  = rev_anom[rev_anom["type"] == "Revenue Drop"]
        if not spikes.empty:
            fig_anom.add_trace(go.Scatter(
                x=spikes["date"], y=spikes["revenue"],
                mode="markers", name="Spike",
                marker=dict(color="#f59e0b", size=10, symbol="triangle-up")))
        if not drops.empty:
            fig_anom.add_trace(go.Scatter(
                x=drops["date"], y=drops["revenue"],
                mode="markers", name="Drop",
                marker=dict(color="#ef4444", size=10, symbol="triangle-down")))
    fig_anom.update_layout(**CHART_THEME, height=320,
                           legend=dict(orientation="h", y=1.05, bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_anom, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 4 — Recommendations
# ─────────────────────────────────────────────────────────────────────────
with tab4:
    recs = recommender.get_all_recommendations()
    summary = recs["summary"]

    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("🚨 Urgent Restocks",   summary["urgent_restocks"])
    col_r2.metric("💰 Pricing Actions",   summary["pricing_actions"])
    col_r3.metric("👥 Retention Actions", summary["retention_actions"])

    # Restock recommendations
    section("🔄", "Restocking Recommendations")
    for r in recs["restock"][:8]:
        urgency_color = {"URGENT":"#ef4444","HIGH":"#f59e0b","MEDIUM":"#60a5fa"}.get(r["urgency"],"#60a5fa")
        st.markdown(f"""
        <div class="rec-card">
            <div class="rec-title">
                <span style="color:{urgency_color}">● {r['urgency']}</span>
                &nbsp;|&nbsp; {r['product']}
            </div>
            <div class="rec-body">
                📦 Current stock: <b>{int(r['current_stock'])}</b> units
                &nbsp;·&nbsp; ⏱ Days remaining: <b>{r['days_of_stock']}</b>
                &nbsp;·&nbsp; 💰 Monthly revenue: <b>${r['monthly_revenue']:,.0f}</b><br>
                ✅ Action: {r['action']}
            </div>
        </div>""", unsafe_allow_html=True)

    # Pricing recommendations
    section("💰", "Pricing Optimization")
    if recs["pricing"]:
        for p in recs["pricing"]:
            st.markdown(f"""
            <div class="rec-card">
                <div class="rec-title">💲 {p['type']} — {p['product']}</div>
                <div class="rec-body">
                    Current: <b>${p['current_price']}</b>
                    → Suggested: <b>${p['suggested_price']}</b><br>
                    Reason: {p['reason']}<br>
                    Impact: <span style="color:#34d399">{p['impact']}</span>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("✅ Pricing looks optimal across all products.")

    # Customer retention
    section("👥", "Customer Retention")
    for c in recs["customer_retention"]:
        pcolor = "#ef4444" if c["priority"] == "HIGH" else "#f59e0b"
        st.markdown(f"""
        <div class="rec-card">
            <div class="rec-title" style="color:{pcolor}">
                {c['segment']} — {c['customer_id']}
            </div>
            <div class="rec-body">
                Inactive for <b>{c['days_inactive']}</b> days
                &nbsp;·&nbsp; Lifetime value: <b>${c['lifetime_value']:,.0f}</b><br>
                ✅ {c['recommended_action']}
            </div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 5 — AI Assistant
# ─────────────────────────────────────────────────────────────────────────
with tab5:
    section("🤖", "AI Business Advisor")

    st.markdown("""
    <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;
                padding:14px 18px;margin-bottom:16px;font-size:13px;color:#94a3b8">
        💡 Ask me anything about your ERP data — sales trends, anomalies, forecasts,
        inventory, customer behaviour, or business strategy.
    </div>
    """, unsafe_allow_html=True)

    # Quick question buttons
    suggestions = [
        "Why did sales drop?",
        "Which product performs best?",
        "Predict next month revenue",
        "What are the inventory risks?",
        "How to improve customer retention?",
    ]
    cols_s = st.columns(len(suggestions))
    quick_q = None
    for i, (col_s, sug) in enumerate(zip(cols_s, suggestions)):
        with col_s:
            if st.button(sug, key=f"sug_{i}", use_container_width=True):
                quick_q = sug

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "api_history" not in st.session_state:
        st.session_state.api_history = []

    # Render existing conversation
    if st.session_state.chat_history:
        st.markdown("<div style='max-height:420px;overflow-y:auto;padding:4px'>", unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">{msg["content"]}</div>'
                            '<div style="clear:both"></div>', unsafe_allow_html=True)
            else:
                source_badge = f'<div class="chat-source">via {msg.get("source","AI")}</div>'
                st.markdown(
                    f'<div class="chat-ai">{msg["content"]}{source_badge}</div>'
                    '<div style="clear:both"></div>',
                    unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Input box
    user_input = st.chat_input("Ask a business question…") or quick_q

    if user_input:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.api_history.append({"role": "user", "content": user_input})

        # Get AI response
        with st.spinner("🧠 Analysing your data..."):
            result = ai_chat.ask(user_input, st.session_state.api_history[:-1])

        answer = result["answer"]
        source = result["source"]

        # Store assistant reply
        st.session_state.chat_history.append({"role": "assistant", "content": answer, "source": source})
        st.session_state.api_history.append({"role": "assistant", "content": answer})

        # Rerender
        st.rerun()

    if st.button("🗑️ Clear Chat", use_container_width=False):
        st.session_state.chat_history = []
        st.session_state.api_history  = []
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────
# TAB 6 — Inventory
# ─────────────────────────────────────────────────────────────────────────
with tab6:
    section("📦", "Inventory Health Dashboard")
    inv_status = analytics.get_inventory_status()

    # Colour-coded inventory table
    risk_colours = {"Critical": "#ef4444", "Low": "#f59e0b", "Healthy": "#34d399"}
    for _, row in inv_status.iterrows():
        colour = risk_colours.get(str(row["risk"]), "#94a3b8")
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
                    background:#111827;border:1px solid #1f2937;border-radius:8px;
                    padding:10px 16px;margin:6px 0;">
            <span style="color:#f1f5f9;font-weight:600;min-width:200px">{row['product_name']}</span>
            <span style="color:#94a3b8;min-width:140px">Stock: <b style="color:#f1f5f9">{int(row['avg_inventory'])}</b> units</span>
            <span style="color:#94a3b8;min-width:160px">Days left: <b style="color:#f1f5f9">{row['days_of_stock']}</b></span>
            <span style="background:{colour}22;border:1px solid {colour};color:{colour};
                         border-radius:20px;padding:3px 12px;font-size:12px;font-weight:600">
                {row['risk']}
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Bubble chart: inventory vs daily sales velocity
    section("🔵", "Inventory vs Sales Velocity")
    fig_bub = px.scatter(
        inv_status,
        x="avg_daily_sales", y="avg_inventory",
        size="days_of_stock", color=inv_status["risk"].astype(str),
        text="product_name",
        color_discrete_map={"Critical":"#ef4444","Low":"#f59e0b","Healthy":"#34d399"},
        labels={"avg_daily_sales":"Daily Sales Velocity","avg_inventory":"Avg Inventory"},
    )
    fig_bub.update_traces(textposition="top center", textfont=dict(size=10, color="#94a3b8"))
    fig_bub.update_layout(**CHART_THEME, height=380,
                          legend=dict(orientation="h", y=1.05, bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_bub, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<hr style="border-color:#1f2937;margin:40px 0 16px">
<div style="text-align:center;font-size:12px;color:#374151;padding-bottom:20px">
    🧠 <b style="color:#4b5563">AI Business Decision Copilot</b>
    &nbsp;·&nbsp; Built with Streamlit · Prophet · Scikit-learn · Plotly
    &nbsp;·&nbsp; Powered by Claude AI
</div>
""", unsafe_allow_html=True)
