import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.dashboard.utils.db import (
    get_companies, get_ratios, get_pl, get_cf, get_pros_cons
)

st.title("🏢 Company Profile & Financial Deep Dive")

# Fetch all companies
df_comps = get_companies()

if df_comps.empty:
    st.error("No companies found in database.")
    st.stop()

# Search Box / Selection
company_options = [f"{row['id']} - {row['company_name']}" for _, row in df_comps.iterrows()]

selected_option = st.selectbox(
    "Search Company by Name or Ticker:",
    options=[""] + company_options,
    index=1 if len(company_options) > 0 else 0,
    help="Type company name or NSE ticker to filter"
)

if not selected_option:
    st.info("Ticker not found — please try another")
    st.stop()

ticker = selected_option.split(" - ")[0].strip()

# Match company info
matching_comp = df_comps[df_comps['id'].str.upper() == ticker.upper()]

if matching_comp.empty:
    st.warning("Ticker not found — please try another")
    st.stop()

comp_info = matching_comp.iloc[0]

# Company Header Card
st.subheader(f"📌 {comp_info['company_name']} ({comp_info['id']})")
col_info1, col_info2, col_info3 = st.columns([2, 1, 1])

with col_info1:
    st.markdown(f"**Broad Sector:** {comp_info.get('broad_sector', 'N/A')}")
    st.markdown(f"**Sub-Sector:** {comp_info.get('sub_sector', 'N/A')}")
    st.markdown(f"**NSE Ticker:** `{comp_info['id']}`")
    about_text = comp_info.get('about_company', '')
    if pd.isna(about_text) or not str(about_text).strip():
        about_text = "No detailed description available."
    st.write(f"**About:** {about_text}")

with col_info2:
    st.markdown(f"**Market Cap Category:** {comp_info.get('market_cap_category', 'N/A')}")
    st.markdown(f"**Book Value:** ₹{comp_info.get('book_value', 'N/A')}")

with col_info3:
    st.markdown(f"**Face Value:** ₹{comp_info.get('face_value', 'N/A')}")
    if comp_info.get('website'):
        st.markdown(f"[🌐 Official Website]({comp_info['website']})")

st.markdown("---")

# Fetch Financial Statement Data
df_ratios = get_ratios(ticker=ticker)
df_pl = get_pl(ticker=ticker)
df_cf = get_cf(ticker=ticker)

# Get Latest Ratios & Metrics
latest_ratio = df_ratios.iloc[-1] if not df_ratios.empty else {}
latest_cf = df_cf.iloc[-1] if not df_cf.empty else {}

roe_val = latest_ratio.get('return_on_equity_pct', np.nan)
roce_val = comp_info.get('roce_percentage', np.nan)
if pd.isna(roce_val) and not df_ratios.empty:
    roce_val = latest_ratio.get('return_on_equity_pct', np.nan) # Fallback

npm_val = latest_ratio.get('net_profit_margin_pct', np.nan)
de_val = latest_ratio.get('debt_to_equity', np.nan)
rev_cagr = latest_ratio.get('revenue_cagr_5yr', np.nan)
fcf_val = latest_ratio.get('free_cash_flow_cr', np.nan)

# Display 6 KPI Tiles
st.subheader("Key Performance Indicators (Latest Year)")
k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.metric("ROE", f"{roe_val:.2f}%" if pd.notna(roe_val) else "N/A")
with k2:
    st.metric("ROCE", f"{roce_val:.2f}%" if pd.notna(roce_val) else "N/A")
with k3:
    st.metric("Net Profit Margin", f"{npm_val:.2f}%" if pd.notna(npm_val) else "N/A")
with k4:
    st.metric("D/E Ratio", f"{de_val:.2f}x" if pd.notna(de_val) else "N/A")
with k5:
    st.metric("Revenue CAGR (5yr)", f"{rev_cagr:.2f}%" if pd.notna(rev_cagr) else "N/A")
with k6:
    st.metric("Free Cash Flow", f"₹{fcf_val:,.1f} Cr" if pd.notna(fcf_val) else "N/A")

st.markdown("---")

# Visualizations: 10-Year Bar Chart (Revenue & Net Profit) and ROE/ROCE Dual Axis Line Chart
chart_c1, chart_c2 = st.columns(2)

with chart_c1:
    st.subheader("10-Year Revenue & Net Profit (₹ Crore)")
    if not df_pl.empty and 'sales' in df_pl.columns and 'net_profit' in df_pl.columns:
        df_pl_clean = df_pl.sort_values(by='year').tail(10)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df_pl_clean['year'].astype(str),
            y=df_pl_clean['sales'],
            name='Revenue (Sales)',
            marker_color='#38bdf8'
        ))
        fig_bar.add_trace(go.Bar(
            x=df_pl_clean['year'].astype(str),
            y=df_pl_clean['net_profit'],
            name='Net Profit',
            marker_color='#4ade80'
        ))
        fig_bar.update_layout(
            barmode='group',
            margin=dict(t=30, b=30, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Insufficient P&L data for revenue bar chart.")

with chart_c2:
    st.subheader("10-Year ROE & ROCE Dual-Axis Trend")
    if not df_ratios.empty and 'return_on_equity_pct' in df_ratios.columns:
        df_ratios_clean = df_ratios.sort_values(by='year').tail(10)
        
        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(
            go.Scatter(
                x=df_ratios_clean['year'].astype(str),
                y=df_ratios_clean['return_on_equity_pct'],
                name='ROE (%)',
                mode='lines+markers',
                line=dict(color='#818cf8', width=3)
            ),
            secondary_y=False
        )
        
        # Check if ROCE percentage column or operating profit margin is available
        roce_col = 'return_on_equity_pct'
        if 'roce_percentage' in df_ratios_clean.columns and not df_ratios_clean['roce_percentage'].isna().all():
            roce_col = 'roce_percentage'
        elif 'operating_profit_margin_pct' in df_ratios_clean.columns:
            roce_col = 'operating_profit_margin_pct'
            
        fig_dual.add_trace(
            go.Scatter(
                x=df_ratios_clean['year'].astype(str),
                y=df_ratios_clean[roce_col],
                name='ROCE / Margin (%)',
                mode='lines+markers',
                line=dict(color='#fbbf24', width=3, dash='dash')
            ),
            secondary_y=True
        )
        
        fig_dual.update_layout(
            margin=dict(t=30, b=30, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_dual.update_yaxes(title_text="ROE (%)", secondary_y=False)
        fig_dual.update_yaxes(title_text="ROCE / Margin (%)", secondary_y=True)
        st.plotly_chart(fig_dual, use_container_width=True)
    else:
        st.info("Insufficient financial ratios data for trend chart.")

st.markdown("---")

# Pros & Cons Section
st.subheader("Pros & Cons Highlights")
df_pc = get_pros_cons(ticker=ticker)

p_col, c_col = st.columns(2)

with p_col:
    st.markdown("##### Green Checks (Pros)")
    if not df_pc.empty and 'pros' in df_pc.columns and pd.notna(df_pc.iloc[0]['pros']):
        pros_raw = str(df_pc.iloc[0]['pros'])
        pros_list = [p.strip() for p in pros_raw.replace('\n', '|').split('|') if p.strip()]
        for item in pros_list:
            st.markdown(f"✔ **{item}**")
    else:
        st.markdown("✔ *Strong fundamentals and sector leadership.*")

with c_col:
    st.markdown("##### Red Crosses (Cons)")
    if not df_pc.empty and 'cons' in df_pc.columns and pd.notna(df_pc.iloc[0]['cons']):
        cons_raw = str(df_pc.iloc[0]['cons'])
        cons_list = [c.strip() for c in cons_raw.replace('\n', '|').split('|') if c.strip()]
        for item in cons_list:
            st.markdown(f"✖ **{item}**")
    else:
        st.markdown("✖ *Monitored for valuation and macro economic cycles.*")
