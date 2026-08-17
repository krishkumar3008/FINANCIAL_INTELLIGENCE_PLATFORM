import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import requests
from src.dashboard.utils.db import get_companies, get_documents

st.title("📄 Annual Reports & Regulatory Filings")

df_comps = get_companies()

if df_comps.empty:
    st.error("No companies found.")
    st.stop()

company_options = [f"{row['id']} - {row['company_name']}" for _, row in df_comps.iterrows()]

selected_comp = st.selectbox("Search Company for Annual Reports:", company_options)
ticker = selected_comp.split(" - ")[0].strip()
comp_name = selected_comp.split(" - ")[1].strip()

st.subheader(f"Annual Reports Archive for {comp_name} ({ticker})")

df_docs = get_documents(ticker=ticker)

if df_docs.empty:
    st.warning("No annual report filings found for this company.")
    st.stop()

# Helper function to check URL health/validity
@st.cache_data(ttl=3600)
def check_url_status(url: str) -> bool:
    if not url or pd.isna(url) or not str(url).startswith("http"):
        return False
    try:
        # Perform quick HEAD request to verify status code
        resp = requests.head(url, timeout=3.0, headers={'User-Agent': 'Mozilla/5.0'})
        return resp.status_code < 400
    except Exception:
        return False

# Display reports in a clean card layout
years_grid = st.columns(3)

for idx, (_, row) in enumerate(df_docs.iterrows()):
    year = row['year']
    url = str(row.get('annual_report', '')).strip()
    
    with years_grid[idx % 3]:
        st.markdown(f"#### 📅 FY {year}")
        if url and url.startswith("http"):
            is_valid = check_url_status(url)
            if is_valid:
                st.markdown(f"📄 [**Download FY {year} Annual Report (PDF)**]({url})")
                st.success("Status: Available")
            else:
                st.markdown(f"🔗 [Link]({url})")
                st.markdown("<span style='background-color:#ef4444; color:white; padding:4px 8px; border-radius:4px; font-weight:bold;'>Report unavailable</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='background-color:#ef4444; color:white; padding:4px 8px; border-radius:4px; font-weight:bold;'>Report unavailable</span>", unsafe_allow_html=True)
        st.markdown("---")

st.subheader("Filings Table View")
st.dataframe(df_docs[['year', 'annual_report']].rename(columns={'year': 'Financial Year', 'annual_report': 'BSE Document Link'}), use_container_width=True, hide_index=True)
