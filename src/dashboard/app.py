import os
import sys
import streamlit as st

# Add project root to sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT_DIR)

st.set_page_config(
    page_title="Nifty 100 Financial Intelligence & AI Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS Injection for Modern Dark Glassmorphism UI & Styling
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif;
        letter-spacing: -0.02em;
    }

    /* Metric Cards Glassmorphism */
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    
    /* Container Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 12px;
    }

    /* Primary Action Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
        transition: all 0.2s ease !important;
    }
    
    button[kind="primary"]:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

pages = [
    st.Page(os.path.join(ROOT_DIR, "pages", "01_home.py"), title="Home", icon="🏠"),
    st.Page(
        os.path.join(ROOT_DIR, "pages", "09_predictor.py"),
        title="AI Market Predictor",
        icon="🤖",
    ),
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
