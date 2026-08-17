import os
import sys

import streamlit as st

# Add project root to sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT_DIR)

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page(os.path.join(ROOT_DIR, "pages", "01_home.py"), title="Home", icon="🏠"),
    st.Page(
        os.path.join(ROOT_DIR, "pages", "02_profile.py"),
        title="Company Profile",
        icon="🏢",
    ),
    st.Page(
        os.path.join(ROOT_DIR, "pages", "03_screener.py"),
        title="Financial Screener",
        icon="🎯",
    ),
    st.Page(
        os.path.join(ROOT_DIR, "pages", "04_peers.py"),
        title="Peer Comparison",
        icon="👥",
    ),
    st.Page(
        os.path.join(ROOT_DIR, "pages", "05_trends.py"),
        title="Trend Analysis",
        icon="📈",
    ),
    st.Page(
        os.path.join(ROOT_DIR, "pages", "06_sectors.py"),
        title="Sector Analysis",
        icon="📊",
    ),
    st.Page(
        os.path.join(ROOT_DIR, "pages", "07_capital.py"),
        title="Capital Allocation Map",
        icon="🗺️",
    ),
    st.Page(
        os.path.join(ROOT_DIR, "pages", "08_reports.py"),
        title="Annual Reports",
        icon="📄",
    ),
]

pg = st.navigation(pages)
pg.run()
