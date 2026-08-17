import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.dashboard.utils.db import get_companies, get_ratios, get_valuation, get_sectors

st.title("🏠 Home — Nifty 100 Financial Overview")

# Sidebar Year Selector
st.sidebar.header("Filter Options")
available_years = list(range(2019, 2025))
selected_year = st.sidebar.selectbox("Select Financial Year:", available_years, index=len(available_years) - 1)

# Fetch Data
df_comps = get_companies()
df_ratios = get_ratios(year=selected_year)
df_val = get_valuation()
if not df_val.empty and 'year' in df_val.columns:
    df_val_year = df_val[df_val['year'] == selected_year]
else:
    df_val_year = pd.DataFrame()

# Merge ratios and market cap for the selected year
df_merged = pd.merge(df_comps[['id', 'company_name', 'broad_sector', 'sub_sector']], df_ratios, left_on='id', right_on='company_id', how='left')
if not df_val_year.empty:
    df_merged = pd.merge(df_merged, df_val_year[['company_id', 'pe_ratio', 'pb_ratio']], on='company_id', how='left')
elif 'pe_ratio' not in df_merged.columns:
    df_merged['pe_ratio'] = np.nan

# Ensure ticker column key exists consistently
if 'company_id' not in df_merged.columns and 'id' in df_merged.columns:
    df_merged['company_id'] = df_merged['id']
elif 'id' not in df_merged.columns and 'company_id' in df_merged.columns:
    df_merged['id'] = df_merged['company_id']

# Calculate KPI Metrics
avg_roe = df_merged['return_on_equity_pct'].dropna().mean() if 'return_on_equity_pct' in df_merged and not df_merged['return_on_equity_pct'].dropna().empty else 0.0
med_pe = df_merged['pe_ratio'].dropna().median() if 'pe_ratio' in df_merged and not df_merged['pe_ratio'].dropna().empty else 0.0
med_de = df_merged['debt_to_equity'].dropna().median() if 'debt_to_equity' in df_merged and not df_merged['debt_to_equity'].dropna().empty else 0.0
total_companies = len(df_comps)
med_rev_cagr = df_merged['revenue_cagr_5yr'].dropna().median() if 'revenue_cagr_5yr' in df_merged and not df_merged['revenue_cagr_5yr'].dropna().empty else 0.0
debt_free_count = len(df_merged[df_merged['debt_to_equity'] <= 0.05]) if 'debt_to_equity' in df_merged else 0

# Render 6 Summary KPI Tiles
st.subheader(f"Financial Summary KPIs ({selected_year})")
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Average ROE", f"{avg_roe:.2f}%")

with col2:
    st.metric("Median P/E", f"{med_pe:.2f}x" if not np.isnan(med_pe) else "N/A")

with col3:
    st.metric("Median D/E", f"{med_de:.2f}x" if not np.isnan(med_de) else "N/A")

with col4:
    st.metric("Total Companies", f"{total_companies}")

with col5:
    st.metric("Median Rev CAGR (5yr)", f"{med_rev_cagr:.2f}%" if not np.isnan(med_rev_cagr) else "N/A")

with col6:
    st.metric("Debt-Free Companies", f"{debt_free_count}")

st.markdown("---")

# Layout: Donut Chart + Top 5 Companies
c_left, c_right = st.columns([1, 1])

with c_left:
    st.subheader("Sector Breakdown (11 Sectors)")
    if 'broad_sector' in df_comps.columns and not df_comps['broad_sector'].isna().all():
        sector_counts = df_comps['broad_sector'].value_counts().reset_index()
        sector_counts.columns = ['broad_sector', 'count']
        
        fig_donut = px.pie(
            sector_counts,
            values='count',
            names='broad_sector',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_donut.update_traces(textinfo='percent+label')
        fig_donut.update_layout(margin=dict(t=30, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("Sector data unavailable.")

with c_right:
    st.subheader("Top 5 Companies by Composite Quality Score")
    if 'composite_quality_score' in df_merged.columns and not df_merged['composite_quality_score'].isna().all():
        df_merged['score_num'] = pd.to_numeric(df_merged['composite_quality_score'], errors='coerce')
        top5 = df_merged.sort_values(by='score_num', ascending=False).head(5)
        
        req_cols = ['company_id', 'company_name', 'broad_sector', 'composite_quality_score', 'return_on_equity_pct', 'debt_to_equity']
        avail_cols = [c for c in req_cols if c in top5.columns]
        disp_top5 = top5[avail_cols].copy()
        
        rename_map = {
            'company_id': 'Ticker',
            'company_name': 'Company Name',
            'broad_sector': 'Sector',
            'composite_quality_score': 'Quality Score',
            'return_on_equity_pct': 'ROE (%)',
            'debt_to_equity': 'D/E (x)'
        }
        disp_top5 = disp_top5.rename(columns=rename_map)
        st.dataframe(disp_top5, use_container_width=True, hide_index=True)
    else:
        # Fallback to sorting by ROE
        top5 = df_merged.sort_values(by='return_on_equity_pct', ascending=False).head(5)
        req_cols = ['company_id', 'company_name', 'broad_sector', 'return_on_equity_pct', 'debt_to_equity']
        avail_cols = [c for c in req_cols if c in top5.columns]
        disp_top5 = top5[avail_cols].copy()
        
        rename_map = {
            'company_id': 'Ticker',
            'company_name': 'Company Name',
            'broad_sector': 'Sector',
            'return_on_equity_pct': 'ROE (%)',
            'debt_to_equity': 'D/E (x)'
        }
        disp_top5 = disp_top5.rename(columns=rename_map)
        st.dataframe(disp_top5, use_container_width=True, hide_index=True)
