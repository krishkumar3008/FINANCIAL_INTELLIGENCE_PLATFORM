import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px
from src.dashboard.utils.db import get_companies, get_capital_allocation, get_ratios

st.title("🗺️ Capital Allocation Pattern Map")

df_cap = get_capital_allocation()
df_comps = get_companies()

if df_cap.empty:
    st.error("Capital allocation dataset not found at output/capital_allocation.csv.")
    st.stop()

# Get latest year capital allocation pattern for each company
df_cap_latest = df_cap.sort_values(by='year').groupby('company_id').last().reset_index()

# Merge with companies metadata
df_merged = pd.merge(df_comps[['id', 'company_name', 'broad_sector', 'sub_sector']], df_cap_latest, left_on='id', right_on='company_id', how='inner')

# Get latest FCF for treemap weighting
df_ratios = get_ratios()
if not df_ratios.empty:
    df_r_latest = df_ratios.sort_values('year').groupby('company_id').last().reset_index()
    df_merged = pd.merge(df_merged, df_r_latest[['company_id', 'free_cash_flow_cr']], on='company_id', how='left')
else:
    df_merged['free_cash_flow_cr'] = 100.0

df_merged['treemap_size'] = df_merged['free_cash_flow_cr'].apply(lambda x: max(abs(x) if pd.notna(x) else 100, 10))

st.subheader("Interactive Capital Allocation Treemap (92 Companies)")
st.caption("Grouped by 8 Capital Allocation Patterns — Size proportional to Absolute FCF (₹ Cr)")

# Plotly Treemap
fig_tree = px.treemap(
    df_merged,
    path=['pattern_label', 'broad_sector', 'company_name'],
    values='treemap_size',
    color='pattern_label',
    hover_data=['id', 'cfo_sign', 'cfi_sign', 'cff_sign', 'free_cash_flow_cr'],
    color_discrete_sequence=px.colors.qualitative.Bold
)
fig_tree.update_layout(margin=dict(t=30, b=10, l=10, r=10))
st.plotly_chart(fig_tree, use_container_width=True)

st.markdown("---")

# Pattern Detail Inspector
st.subheader("Filter & Inspect Companies by Capital Allocation Pattern")

patterns = sorted(df_merged['pattern_label'].unique().tolist())
selected_pattern = st.selectbox("Select Capital Allocation Pattern:", ["All Patterns"] + patterns)

if selected_pattern != "All Patterns":
    pattern_filtered = df_merged[df_merged['pattern_label'] == selected_pattern]
else:
    pattern_filtered = df_merged

st.info(f"Showing **{len(pattern_filtered)} companies** classified under pattern: **{selected_pattern}**")

disp_cols = ['company_id', 'company_name', 'broad_sector', 'pattern_label', 'cfo_sign', 'cfi_sign', 'cff_sign', 'free_cash_flow_cr']
df_disp = pattern_filtered[disp_cols].copy()
df_disp.columns = ['Ticker', 'Company Name', 'Sector', 'Pattern Label', 'CFO Sign', 'CFI Sign', 'CFF Sign', 'FCF (₹ Cr)']

st.dataframe(df_disp, use_container_width=True, hide_index=True)
