import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.dashboard.utils.db import get_peers, get_ratios, get_companies

st.title("👥 Peer Comparison & Radar Analytics")

df_peers_all = get_peers()

if df_peers_all.empty:
    st.error("No peer groups found in database.")
    st.stop()

peer_groups = sorted(df_peers_all['peer_group_name'].dropna().unique())

# Peer Group Selection Dropdown
selected_group = st.selectbox("Select Peer Group (11 Groups Available):", peer_groups)

group_members = df_peers_all[df_peers_all['peer_group_name'] == selected_group].copy()

# Load latest ratios for all members in the group
df_ratios = get_ratios()
if not df_ratios.empty:
    df_ratios_latest = df_ratios.sort_values('year').groupby('company_id').last().reset_index()
else:
    df_ratios_latest = pd.DataFrame()

df_merged_group = pd.merge(group_members, df_ratios_latest, left_on='company_id', right_on='company_id', how='left')

st.subheader(f"Peer Group Overview: {selected_group} ({len(df_merged_group)} Companies)")

bm_row = df_merged_group[df_merged_group['is_benchmark'] == 1]
if not bm_row.empty:
    bm_name = bm_row.iloc[0]['company_name']
    st.success(f"⭐ **Benchmark Company for {selected_group}:** {bm_name} ({bm_row.iloc[0]['company_id']})")

# Select Target Company for Radar Comparison
target_company_options = [f"{row['company_id']} - {row['company_name']}" for _, row in df_merged_group.iterrows()]
selected_target = st.selectbox("Select Company for 8-Axis Radar Chart:", target_company_options)

target_id = selected_target.split(" - ")[0].strip()

# 8 Metrics for Radar Chart
radar_metrics_map = {
    'ROE (%)': 'return_on_equity_pct',
    'OPM (%)': 'operating_profit_margin_pct',
    'NPM (%)': 'net_profit_margin_pct',
    'D/E (x)': 'debt_to_equity',
    'Rev CAGR 5yr (%)': 'revenue_cagr_5yr',
    'PAT CAGR 5yr (%)': 'pat_cagr_5yr',
    'FCF (Cr)': 'free_cash_flow_cr',
    'ICR (x)': 'interest_coverage'
}

categories = list(radar_metrics_map.keys())

target_values = []
peer_avg_values = []

target_row = df_merged_group[df_merged_group['company_id'] == target_id]

for label, col in radar_metrics_map.items():
    if col in df_merged_group.columns:
        avg_val = df_merged_group[col].dropna().mean()
        peer_avg_values.append(float(avg_val) if pd.notna(avg_val) else 0.0)
        
        if not target_row.empty and col in target_row.columns and pd.notna(target_row.iloc[0][col]):
            target_values.append(float(target_row.iloc[0][col]))
        else:
            target_values.append(0.0)
    else:
        peer_avg_values.append(0.0)
        target_values.append(0.0)

# Normalize metrics for radar display if values vary wildly in scale
def min_max_normalize(val_list, ref_list):
    norm = []
    for v, r in zip(val_list, ref_list):
        max_val = max(abs(v), abs(r), 1.0)
        norm.append(round((v / max_val) * 100, 2))
    return norm

# Plotly Radar Chart (Scatterpolar)
fig_radar = go.Figure()

fig_radar.add_trace(go.Scatterpolar(
    r=target_values,
    theta=categories,
    fill='toself',
    name=f"{target_id} (Selected Company)",
    line_color='#38bdf8'
))

fig_radar.add_trace(go.Scatterpolar(
    r=peer_avg_values,
    theta=categories,
    fill='toself',
    name=f"{selected_group} Average",
    line_color='#f59e0b'
))

fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, showticklabels=True)),
    showlegend=True,
    title=f"8-Metric Radar Comparison: {target_id} vs {selected_group} Peer Average",
    margin=dict(t=50, b=30, l=30, r=30)
)

st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("---")

# Side-by-Side KPI Table with Benchmark Highlighted
st.subheader(f"Side-by-Side KPI Comparison Table ({selected_group})")

kpi_cols = [
    'company_id', 'company_name', 'is_benchmark', 'return_on_equity_pct',
    'operating_profit_margin_pct', 'net_profit_margin_pct', 'debt_to_equity',
    'revenue_cagr_5yr', 'pat_cagr_5yr', 'free_cash_flow_cr', 'interest_coverage'
]

avail_cols = [c for c in kpi_cols if c in df_merged_group.columns]
df_table = df_merged_group[avail_cols].copy()

# Highlight function for Streamlit DataFrame
def highlight_benchmark(row):
    if row.get('is_benchmark') == 1:
        return ['background-color: #1e3a8a; color: #ffffff; font-weight: bold'] * len(row)
    return [''] * len(row)

styled_df = df_table.style.apply(highlight_benchmark, axis=1)
st.dataframe(styled_df, use_container_width=True, hide_index=True)
