import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.database import get_db_connection
from src.dashboard.utils.db import get_companies
from src.analytics.predictor import predict_stock_tomorrow, get_top_forecasts, compute_technical_indicators
from src.etl.live_updater import fetch_and_update_prices

st.set_page_config(page_title="AI Market Predictor", page_icon="🤖", layout="wide")

# Modern Title Banner
st.markdown("""
<div style="background: linear-gradient(135deg, rgba(15,23,42,0.9) 0%, rgba(30,41,59,0.9) 100%); padding: 24px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 24px;">
    <h1 style="color: #38bdf8; margin: 0; font-size: 2.2rem; font-weight: 700;">🤖 AI Market Predictor & Quantitative Engine</h1>
    <p style="color: #94a3b8; margin-top: 6px; font-size: 1.05rem;">Next-day market opening price forecasts, closing targets, directional signals, and technical momentum powered by Machine Learning.</p>
</div>
""", unsafe_allow_html=True)

# Top Bar & Live Update Action
col_hdr1, col_hdr2 = st.columns([3, 1])

with col_hdr2:
    if st.button("🔄 Refresh Live Market Data", type="primary", use_container_width=True):
        with st.spinner("Fetching latest stock prices from Yahoo Finance..."):
            count = fetch_and_update_prices()
            st.success(f"Updated {count:,} stock price records up to today!")
            st.rerun()

# ----------------------------------------------------
# SECTION 1: TOP MARKET FORECASTS FOR TOMORROW
# ----------------------------------------------------
st.markdown("<h2 style='color: #f8fafc; font-size: 1.5rem;'>🔥 Top Market Setups for Tomorrow</h2>", unsafe_allow_html=True)

def load_top_forecasts():
    return get_top_forecasts(top_n=4)

with st.spinner("Analyzing Nifty 100 constituent predictions..."):
    top_data = load_top_forecasts()

col_bull, col_bear = st.columns(2)

with col_bull:
    st.markdown("#### 🟢 Top Bullish Candidates")
    for b in top_data.get("top_bullish", []):
        open_p = b.get("predicted_open_price", b.get("current_close", 0.0))
        gap_t = b.get("gap_type", "")
        with st.container(border=True):
            st.markdown(f"**{b['company_id']}** — *{b['company_name'].strip()}*")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"Confidence<br><strong style='color:#4ade80;'>{b['confidence_pct']}%</strong>", unsafe_allow_html=True)
            c2.markdown(f"Forecast Open<br><strong style='color:#38bdf8;'>₹{open_p:,.2f} ({gap_t})</strong>", unsafe_allow_html=True)
            c3.markdown(f"Target Close<br><strong style='color:#38bdf8;'>₹{b['predicted_target_close']:,.2f} ({b['expected_change_pct']:+.1f}%)</strong>", unsafe_allow_html=True)

with col_bear:
    st.markdown("#### 🔴 Top Bearish Candidates")
    for b in top_data.get("top_bearish", []):
        open_p = b.get("predicted_open_price", b.get("current_close", 0.0))
        gap_t = b.get("gap_type", "")
        with st.container(border=True):
            st.markdown(f"**{b['company_id']}** — *{b['company_name'].strip()}*")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"Confidence<br><strong style='color:#f87171;'>{b['confidence_pct']}%</strong>", unsafe_allow_html=True)
            c2.markdown(f"Forecast Open<br><strong style='color:#38bdf8;'>₹{open_p:,.2f} ({gap_t})</strong>", unsafe_allow_html=True)
            c3.markdown(f"Target Close<br><strong style='color:#38bdf8;'>₹{b['predicted_target_close']:,.2f} ({b['expected_change_pct']:+.1f}%)</strong>", unsafe_allow_html=True)

st.divider()

# ----------------------------------------------------
# SECTION 2: SINGLE STOCK DEEP DIVE PREDICTION
# ----------------------------------------------------
st.markdown("<h2 style='color: #f8fafc; font-size: 1.5rem;'>🎯 Single Stock Deep Dive & Technical Indicators</h2>", unsafe_allow_html=True)

df_comps = get_companies()
if df_comps.empty:
    st.error("No company records found in database.")
    st.stop()

company_options = [f"{row['id']} - {row['company_name'].strip()}" for _, row in df_comps.iterrows()]
selected_comp = st.selectbox("Select Nifty 100 Company:", company_options, index=0)
ticker = selected_comp.split(" - ")[0].strip()

# Run Prediction Model
pred = predict_stock_tomorrow(ticker)

if "error" in pred:
    st.error(pred["error"])
else:
    # Summary Metrics Grid (6 Metric Cards)
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    
    current_c = pred.get("current_close", 0.0)
    as_of = pred.get("as_of_date", "")
    open_p = pred.get("predicted_open_price", current_c)
    gap_t = pred.get("gap_type", "FLAT OPEN ⚖️")
    gap_pct = pred.get("expected_gap_pct", 0.0)
    direction = pred.get("direction", "BULLISH")
    conf_pct = pred.get("confidence_pct", 50.0)
    target_c = pred.get("predicted_target_close", current_c)
    change_pct = pred.get("expected_change_pct", 0.0)
    stop_l = pred.get("stop_loss", current_c)
    sup = pred.get("support_20d", 0.0)
    res = pred.get("resistance_20d", 0.0)
    rsi_val = pred.get("rsi_14", 50.0)
    prob_bull = pred.get("prob_bullish", 50.0)
    prob_bear = pred.get("prob_bearish", 50.0)

    dir_icon = "🟢" if direction == "BULLISH" else "🔴"
    
    m1.metric("Current Close", f"₹{current_c:,.2f}", f"As of {as_of}")
    m2.metric("Tomorrow Open Price", f"₹{open_p:,.2f}", f"{gap_t} ({gap_pct:+.2f}%)")
    m3.metric("Tomorrow Direction", f"{dir_icon} {direction}", f"{conf_pct}% Confidence")
    m4.metric("Target Close Price", f"₹{target_c:,.2f}", f"{change_pct:+.2f}%")
    m5.metric("Stop-Loss Bounds", f"₹{stop_l:,.2f}")
    m6.metric("Support / Resistance", f"₹{sup} / ₹{res}")

    col_chart, col_signals = st.columns([3, 1])

    with col_signals:
        st.markdown("#### ⚡ Quantitative Signals")
        st.markdown(f"**Predicted Open**: `₹{open_p:,.2f}`")
        st.markdown(f"**Opening Gap**: `{gap_t}` (`{gap_pct:+.2f}%`)")
        st.markdown(f"**RSI (14)**: `{rsi_val}`")
        st.markdown(f"**Bullish Prob**: `{prob_bull}%`")
        st.markdown(f"**Bearish Prob**: `{prob_bear}%`")
        
        st.markdown("#### 📌 Key Indicators")
        for sig in pred.get("key_signals", []):
            st.info(f"✔ {sig}")

    with col_chart:
        # Fetch stock price history for Plotly Chart
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            rows = cursor.execute(
                "SELECT date, open_price, high_price, low_price, close_price, volume FROM stock_prices WHERE company_id=? ORDER BY date ASC",
                (ticker,)
            ).fetchall()
            df_hist = pd.DataFrame([dict(r) for r in rows])
        finally:
            conn.close()

        if not df_hist.empty and len(df_hist) >= 20:
            df_hist = compute_technical_indicators(df_hist)
            chart_df = df_hist.tail(120).copy()

            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                vertical_spacing=0.08, subplot_titles=(f"{ticker} Historical Price, Moving Averages & Bollinger Bands", "RSI (14) Momentum Indicator"),
                row_width=[0.3, 0.7]
            )

            # Price Line
            fig.add_trace(
                go.Scatter(x=chart_df["date"], y=chart_df["close_price"], mode="lines", name="Close Price", line=dict(color="#38bdf8", width=2.5)),
                row=1, col=1
            )
            # 20 SMA & 50 SMA
            fig.add_trace(
                go.Scatter(x=chart_df["date"], y=chart_df["sma_20"], mode="lines", name="20-SMA", line=dict(color="#f59e0b", width=1.5, dash="dash")),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=chart_df["date"], y=chart_df["sma_50"], mode="lines", name="50-SMA", line=dict(color="#a855f7", width=1.5, dash="dot")),
                row=1, col=1
            )
            # Bollinger Bands
            fig.add_trace(
                go.Scatter(x=chart_df["date"], y=chart_df["bb_upper"], mode="lines", name="BB Upper", line=dict(color="#64748b", width=1)),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=chart_df["date"], y=chart_df["bb_lower"], mode="lines", name="BB Lower", line=dict(color="#64748b", width=1), fill="tonexty", fillcolor="rgba(100, 116, 139, 0.12)"),
                row=1, col=1
            )

            # RSI Subplot
            fig.add_trace(
                go.Scatter(x=chart_df["date"], y=chart_df["rsi_14"], mode="lines", name="RSI (14)", line=dict(color="#ec4899", width=2)),
                row=2, col=1
            )
            fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#22c55e", row=2, col=1)

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=40, b=20, l=20, r=20),
                height=460,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)
