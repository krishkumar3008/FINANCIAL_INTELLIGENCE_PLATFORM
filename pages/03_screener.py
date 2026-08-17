import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
from src.dashboard.utils.db import get_companies, get_ratios, get_valuation, get_pl

st.title("🎯 Interactive Financial Screener")

# Initialize Session State for Sliders
default_slider_values = {
    'roe_min': 0.0,
    'de_max': 5.0,
    'fcf_min': -10000.0,
    'rev_cagr_min': -20.0,
    'pat_cagr_min': -20.0,
    'opm_min': 0.0,
    'pe_max': 150.0,
    'pb_max': 50.0,
    'div_yield_min': 0.0,
    'icr_min': 0.0
}

for key, val in default_slider_values.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Preset Buttons Handler
def apply_preset(preset_type):
    if preset_type == "Quality":
        st.session_state['roe_min'] = 18.0
        st.session_state['de_max'] = 0.5
        st.session_state['opm_min'] = 15.0
        st.session_state['icr_min'] = 5.0
        st.session_state['fcf_min'] = 100.0
        st.session_state['pe_max'] = 60.0
        st.session_state['pb_max'] = 15.0
        st.session_state['rev_cagr_min'] = 8.0
        st.session_state['pat_cagr_min'] = 8.0
        st.session_state['div_yield_min'] = 0.0
    elif preset_type == "Value":
        st.session_state['pe_max'] = 25.0
        st.session_state['pb_max'] = 3.0
        st.session_state['div_yield_min'] = 1.5
        st.session_state['de_max'] = 1.0
        st.session_state['roe_min'] = 10.0
        st.session_state['opm_min'] = 8.0
        st.session_state['icr_min'] = 2.0
        st.session_state['fcf_min'] = 0.0
        st.session_state['rev_cagr_min'] = 0.0
        st.session_state['pat_cagr_min'] = 0.0
    elif preset_type == "Growth":
        st.session_state['rev_cagr_min'] = 12.0
        st.session_state['pat_cagr_min'] = 12.0
        st.session_state['roe_min'] = 15.0
        st.session_state['opm_min'] = 12.0
        st.session_state['de_max'] = 2.0
        st.session_state['pe_max'] = 100.0
        st.session_state['pb_max'] = 30.0
        st.session_state['icr_min'] = 3.0
        st.session_state['fcf_min'] = -1000.0
        st.session_state['div_yield_min'] = 0.0
    elif preset_type == "Dividend":
        st.session_state['div_yield_min'] = 2.5
        st.session_state['fcf_min'] = 200.0
        st.session_state['de_max'] = 1.0
        st.session_state['roe_min'] = 12.0
        st.session_state['opm_min'] = 10.0
        st.session_state['pe_max'] = 40.0
        st.session_state['pb_max'] = 10.0
        st.session_state['icr_min'] = 3.0
        st.session_state['rev_cagr_min'] = 0.0
        st.session_state['pat_cagr_min'] = 0.0
    elif preset_type == "Debt-Free":
        st.session_state['de_max'] = 0.05
        st.session_state['roe_min'] = 12.0
        st.session_state['icr_min'] = 10.0
        st.session_state['opm_min'] = 10.0
        st.session_state['fcf_min'] = 50.0
        st.session_state['pe_max'] = 80.0
        st.session_state['pb_max'] = 25.0
        st.session_state['rev_cagr_min'] = 5.0
        st.session_state['pat_cagr_min'] = 5.0
        st.session_state['div_yield_min'] = 0.0
    elif preset_type == "Turnaround":
        st.session_state['pat_cagr_min'] = 15.0
        st.session_state['fcf_min'] = 50.0
        st.session_state['opm_min'] = 8.0
        st.session_state['roe_min'] = 5.0
        st.session_state['de_max'] = 2.5
        st.session_state['pe_max'] = 50.0
        st.session_state['pb_max'] = 15.0
        st.session_state['rev_cagr_min'] = 2.0
        st.session_state['div_yield_min'] = 0.0
        st.session_state['icr_min'] = 1.5

# Sidebar Controls
st.sidebar.header("🎯 Preset Screening Filters")

preset_cols = st.sidebar.columns(2)
with preset_cols[0]:
    if st.button("Quality", use_container_width=True):
        apply_preset("Quality")
        st.rerun()
    if st.button("Growth", use_container_width=True):
        apply_preset("Growth")
        st.rerun()
    if st.button("Debt-Free", use_container_width=True):
        apply_preset("Debt-Free")
        st.rerun()
with preset_cols[1]:
    if st.button("Value", use_container_width=True):
        apply_preset("Value")
        st.rerun()
    if st.button("Dividend", use_container_width=True):
        apply_preset("Dividend")
        st.rerun()
    if st.button("Turnaround", use_container_width=True):
        apply_preset("Turnaround")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📊 Filter Sliders")

st.session_state['roe_min'] = st.sidebar.slider("Minimum ROE (%)", -50.0, 100.0, st.session_state['roe_min'], 1.0)
st.session_state['de_max'] = st.sidebar.slider("Maximum D/E Ratio (x)", 0.0, 10.0, st.session_state['de_max'], 0.1)
st.session_state['fcf_min'] = st.sidebar.slider("Minimum FCF (₹ Cr)", -10000.0, 50000.0, st.session_state['fcf_min'], 100.0)
st.session_state['rev_cagr_min'] = st.sidebar.slider("Minimum Revenue CAGR 5yr (%)", -30.0, 100.0, st.session_state['rev_cagr_min'], 1.0)
st.session_state['pat_cagr_min'] = st.sidebar.slider("Minimum PAT CAGR 5yr (%)", -30.0, 100.0, st.session_state['pat_cagr_min'], 1.0)
st.session_state['opm_min'] = st.sidebar.slider("Minimum OPM (%)", -20.0, 100.0, st.session_state['opm_min'], 1.0)
st.session_state['pe_max'] = st.sidebar.slider("Maximum P/E Ratio (x)", 0.0, 200.0, st.session_state['pe_max'], 1.0)
st.session_state['pb_max'] = st.sidebar.slider("Maximum P/B Ratio (x)", 0.0, 100.0, st.session_state['pb_max'], 0.5)
st.session_state['div_yield_min'] = st.sidebar.slider("Minimum Dividend Yield (%)", 0.0, 15.0, st.session_state['div_yield_min'], 0.1)
st.session_state['icr_min'] = st.sidebar.slider("Minimum ICR (x)", 0.0, 50.0, st.session_state['icr_min'], 0.5)

# Load Latest Universe Data
df_comps = get_companies()
df_ratios = get_ratios()
df_val = get_valuation()

# Get latest year for each company ratio and valuation
if not df_ratios.empty:
    df_ratios_latest = df_ratios.sort_values('year').groupby('company_id').last().reset_index()
else:
    df_ratios_latest = pd.DataFrame()

if not df_val.empty:
    df_val_latest = df_val.sort_values('year').groupby('company_id').last().reset_index()
else:
    df_val_latest = pd.DataFrame()

# Merge Universe
df_universe = pd.merge(df_comps, df_ratios_latest, left_on='id', right_on='company_id', how='inner')
if not df_val_latest.empty:
    df_universe = pd.merge(df_universe, df_val_latest[['company_id', 'pe_ratio', 'pb_ratio', 'dividend_yield_pct']], on='company_id', how='left')

# Apply Filtering Conditions
mask = (
    (df_universe['return_on_equity_pct'].fillna(-999) >= st.session_state['roe_min']) &
    (df_universe['debt_to_equity'].fillna(999) <= st.session_state['de_max']) &
    (df_universe['free_cash_flow_cr'].fillna(-99999) >= st.session_state['fcf_min']) &
    (df_universe['revenue_cagr_5yr'].fillna(-999) >= st.session_state['rev_cagr_min']) &
    (df_universe['pat_cagr_5yr'].fillna(-999) >= st.session_state['pat_cagr_min']) &
    (df_universe['operating_profit_margin_pct'].fillna(-999) >= st.session_state['opm_min']) &
    (df_universe['pe_ratio'].fillna(999) <= st.session_state['pe_max']) &
    (df_universe['pb_ratio'].fillna(999) <= st.session_state['pb_max']) &
    (df_universe['dividend_yield_pct'].fillna(-999) >= st.session_state['div_yield_min']) &
    (df_universe['interest_coverage'].fillna(-999) >= st.session_state['icr_min'])
)

df_filtered = df_universe[mask].copy()

# Header & Result Count Label
st.success(f"🔍 **{len(df_filtered)} companies match your filters** out of {len(df_universe)} total companies.")

# Download CSV Section
col_dl1, col_dl2 = st.columns([3, 1])

display_columns = [
    'company_id', 'company_name', 'broad_sector', 'composite_quality_score',
    'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr',
    'revenue_cagr_5yr', 'pat_cagr_5yr', 'operating_profit_margin_pct',
    'pe_ratio', 'pb_ratio', 'dividend_yield_pct', 'interest_coverage'
]

available_display_cols = [c for c in display_columns if c in df_filtered.columns]
df_display = df_filtered[available_display_cols].copy()

# Rename for clean output presentation
rename_dict = {
    'company_id': 'Ticker',
    'company_name': 'Company Name',
    'broad_sector': 'Sector',
    'composite_quality_score': 'Quality Score',
    'return_on_equity_pct': 'ROE (%)',
    'debt_to_equity': 'D/E (x)',
    'free_cash_flow_cr': 'FCF (₹ Cr)',
    'revenue_cagr_5yr': 'Rev CAGR 5yr (%)',
    'pat_cagr_5yr': 'PAT CAGR 5yr (%)',
    'operating_profit_margin_pct': 'OPM (%)',
    'pe_ratio': 'P/E (x)',
    'pb_ratio': 'P/B (x)',
    'dividend_yield_pct': 'Div Yield (%)',
    'interest_coverage': 'ICR (x)'
}

df_display_renamed = df_display.rename(columns=rename_dict)

with col_dl2:
    csv_data = df_display_renamed.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export CSV",
        data=csv_data,
        file_name="screener_results.csv",
        mime="text/csv",
        use_container_width=True
    )

# Display Results Table
st.dataframe(df_display_renamed, use_container_width=True, hide_index=True)
