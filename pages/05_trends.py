import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.dashboard.utils.db import get_companies, get_pl, get_ratios, get_bs, get_cf

st.title("📈 Multi-Metric Financial Trend Analysis")

df_comps = get_companies()
if df_comps.empty:
    st.error("No companies found.")
    st.stop()

company_options = [f"{row['id']} - {row['company_name']}" for _, row in df_comps.iterrows()]

col_s1, col_s2 = st.columns([1, 2])

with col_s1:
    selected_comp = st.selectbox("Select Company:", company_options)
    ticker = selected_comp.split(" - ")[0].strip()

# Fetch All Historical Statements
df_pl = get_pl(ticker=ticker)
df_ratios = get_ratios(ticker=ticker)
df_bs = get_bs(ticker=ticker)
df_cf = get_cf(ticker=ticker)

# Merge statements by year
df_merged = pd.merge(df_pl, df_ratios, on=['company_id', 'year'], how='outer', suffixes=('', '_ratio'))
df_merged = pd.merge(df_merged, df_bs, on=['company_id', 'year'], how='outer', suffixes=('', '_bs'))
df_merged = df_merged.sort_values(by='year').tail(10)

metric_options = {
    "Revenue (Sales ₹ Cr)": "sales",
    "Net Profit (₹ Cr)": "net_profit",
    "Operating Profit (₹ Cr)": "operating_profit",
    "ROE (%)": "return_on_equity_pct",
    "OPM (%)": "operating_profit_margin_pct",
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "Free Cash Flow (₹ Cr)": "free_cash_flow_cr",
    "Borrowings / Debt (₹ Cr)": "borrowings"
}

with col_s2:
    selected_metric_labels = st.multiselect(
        "Select up to 3 Metrics to Overlay:",
        options=list(metric_options.keys()),
        default=["Revenue (Sales ₹ Cr)", "Net Profit (₹ Cr)"],
        max_selections=3
    )

if not selected_metric_labels:
    st.warning("Please select at least 1 metric to visualize trends.")
    st.stop()

# Plot 10-Year Line Chart with YoY Annotations
fig = go.Figure()

colors = ['#38bdf8', '#4ade80', '#f59e0b']

for i, label in enumerate(selected_metric_labels):
    col_name = metric_options[label]
    if col_name in df_merged.columns:
        sub_df = df_merged[['year', col_name]].dropna().sort_values(by='year')
        if not sub_df.empty:
            y_vals = sub_df[col_name].values
            years = sub_df['year'].astype(str).values
            
            # Compute YoY % Change
            yoy_text = []
            for idx in range(len(y_vals)):
                if idx == 0 or y_vals[idx - 1] == 0 or pd.isna(y_vals[idx - 1]):
                    yoy_text.append(f"{y_vals[idx]:,.1f}")
                else:
                    pct = ((y_vals[idx] - y_vals[idx - 1]) / abs(y_vals[idx - 1])) * 100
                    sign = "+" if pct >= 0 else ""
                    yoy_text.append(f"{y_vals[idx]:,.1f}<br>({sign}{pct:.1f}%)")
            
            fig.add_trace(go.Scatter(
                x=years,
                y=y_vals,
                mode='lines+markers+text',
                name=label,
                text=yoy_text,
                textposition="top center",
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=8)
            ))

fig.update_layout(
    title=f"10-Year Multi-Metric Trend Analysis for {ticker} (with YoY % Changes)",
    xaxis_title="Financial Year",
    yaxis_title="Metric Value",
    margin=dict(t=50, b=30, l=30, r=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# Data Table Display
st.subheader("Historical Data Table")
disp_cols = ['year'] + [metric_options[l] for l in selected_metric_labels if metric_options[l] in df_merged.columns]
st.dataframe(df_merged[disp_cols].rename(columns={'year': 'Year'}), use_container_width=True, hide_index=True)
