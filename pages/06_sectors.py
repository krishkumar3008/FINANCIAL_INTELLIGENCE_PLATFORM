import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.dashboard.utils.db import get_companies, get_ratios, get_valuation, get_pl

st.title("📊 Sector Analysis & Positioning")

df_comps = get_companies()
df_ratios = get_ratios()
df_val = get_valuation()
df_pl = get_pl()

if df_comps.empty:
    st.error("No company data available.")
    st.stop()

# Latest year data per company
df_ratios_latest = df_ratios.sort_values('year').groupby('company_id').last().reset_index() if not df_ratios.empty else pd.DataFrame()
df_val_latest = df_val.sort_values('year').groupby('company_id').last().reset_index() if not df_val.empty else pd.DataFrame()
df_pl_latest = df_pl.sort_values('year').groupby('company_id').last().reset_index() if not df_pl.empty else pd.DataFrame()

# Merge all into sector universe
df_sector_df = pd.merge(df_comps, df_ratios_latest[['company_id', 'return_on_equity_pct', 'operating_profit_margin_pct', 'debt_to_equity']], left_on='id', right_on='company_id', how='left')
if not df_pl_latest.empty:
    df_sector_df = pd.merge(df_sector_df, df_pl_latest[['company_id', 'sales', 'net_profit']], on='company_id', how='left')
if not df_val_latest.empty:
    df_sector_df = pd.merge(df_sector_df, df_val_latest[['company_id', 'market_cap_crore', 'pe_ratio']], on='company_id', how='left')

# Drop missing critical columns for bubble chart
df_sector_df['sales'] = pd.to_numeric(df_sector_df['sales'], errors='coerce').fillna(100)
df_sector_df['return_on_equity_pct'] = pd.to_numeric(df_sector_df['return_on_equity_pct'], errors='coerce').fillna(0)
df_sector_df['market_cap_crore'] = pd.to_numeric(df_sector_df['market_cap_crore'], errors='coerce').fillna(1000)
df_sector_df['market_cap_bubble'] = df_sector_df['market_cap_crore'].apply(lambda x: max(x, 100))

sectors_list = ["All Sectors"] + sorted(df_sector_df['broad_sector'].dropna().unique().tolist())

selected_sector = st.selectbox("Filter Broad Sector:", sectors_list)

if selected_sector != "All Sectors":
    filtered_df = df_sector_df[df_sector_df['broad_sector'] == selected_sector].copy()
else:
    filtered_df = df_sector_df.copy()

st.subheader(f"Bubble Positioning Map: {selected_sector} ({len(filtered_df)} Companies)")
st.caption("X-Axis: Revenue (Sales ₹ Cr) | Y-Axis: ROE (%) | Bubble Size: Market Cap (₹ Cr) | Colour: Sub-Sector")

# Bubble Chart
fig_bubble = px.scatter(
    filtered_df,
    x='sales',
    y='return_on_equity_pct',
    size='market_cap_bubble',
    color='sub_sector',
    hover_name='company_name',
    hover_data=['id', 'broad_sector', 'sub_sector', 'market_cap_crore', 'pe_ratio'],
    text='id',
    size_max=60,
    labels={'sales': 'Revenue (Sales ₹ Cr)', 'return_on_equity_pct': 'ROE (%)'}
)
fig_bubble.update_traces(textposition='top center')
fig_bubble.update_layout(margin=dict(t=30, b=30, l=30, r=30))
st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("---")

# Sector Median KPI Bar Chart Below Bubble Chart
st.subheader("Sector Median KPI Comparison")

median_kpis = df_sector_df.groupby('broad_sector').agg({
    'return_on_equity_pct': 'median',
    'operating_profit_margin_pct': 'median',
    'debt_to_equity': 'median',
    'pe_ratio': 'median'
}).reset_index()

median_kpis.columns = ['Broad Sector', 'Median ROE (%)', 'Median OPM (%)', 'Median D/E (x)', 'Median P/E (x)']

fig_sector_bar = px.bar(
    median_kpis,
    x='Broad Sector',
    y=['Median ROE (%)', 'Median OPM (%)', 'Median P/E (x)'],
    barmode='group',
    title="Sector Median Fundamentals (ROE, OPM, P/E)"
)
fig_sector_bar.update_layout(margin=dict(t=40, b=30, l=30, r=30))
st.plotly_chart(fig_sector_bar, use_container_width=True)

st.dataframe(median_kpis, use_container_width=True, hide_index=True)
