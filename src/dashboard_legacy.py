import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.peer import (
    get_peer_metrics_universe,
)
from src.database import get_db_connection
from src.screener.engine import (
    apply_screener_filter,
    calculate_composite_score,
    get_screener_universe,
    load_screener_config,
)

st.set_page_config(
    page_title="Nifty 100 Financial Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom dark-theme CSS
st.markdown(
    """
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stApp { background-color: #0f172a; color: #f8fafc; }
    h1, h2, h3 { color: #38bdf8 !important; }
    .metric-card {
        background-color: #1e293b;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #334155;
        margin-bottom: 12px;
    }
    .stTable { background-color: #1e293b; }
</style>
""",
    unsafe_allow_html=True,
)


def query_db(query: str, args: tuple = ()) -> pd.DataFrame:
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(query, conn, params=args)
        return df
    finally:
        conn.close()


st.title("📊 Nifty 100 Financial Intelligence Platform")
st.caption("Sprint 3 — Financial Screener, Peer Percentile Engine & Radar Analytics")

main_tabs = st.tabs(
    [
        "🎯 Financial Screener",
        "👥 Peer Comparison Engine",
        "🕸️ Radar Charts",
        "📈 Single Company Deep Dive",
    ]
)

# ----------------- TAB 1: Financial Screener -----------------
with main_tabs[0]:
    st.header("🎯 Financial Screener Core")
    config = load_screener_config()
    presets_cfg = config.get("presets", {})

    col_p1, col_p2 = st.columns([1, 2])

    with col_p1:
        preset_options = {cfg["name"]: key for key, cfg in presets_cfg.items()}
        selected_preset_name = st.selectbox(
            "Select Screener Preset:", list(preset_options.keys())
        )
        selected_key = preset_options[selected_preset_name]
        preset_info = presets_cfg[selected_key]

        st.info(f"**Description:** {preset_info.get('description', '')}")
        st.markdown("**Active Filter Conditions:**")
        for k, v in preset_info.get("filters", {}).items():
            st.markdown(f"- `{k}`: `{v}`")

    df_universe = get_screener_universe()
    df_scored = calculate_composite_score(df_universe, config)
    df_filtered = apply_screener_filter(df_scored, selected_key, config)

    with col_p2:
        st.metric(
            "Companies Passing Screener", f"{len(df_filtered)} / {len(df_scored)}"
        )

    st.subheader(
        f"Screening Results: {selected_preset_name} ({len(df_filtered)} Companies)"
    )

    display_cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "composite_quality_score",
        "sector_relative_composite_score",
        "return_on_equity_pct",
        "roce_percentage",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "sales",
    ]
    disp_df = df_filtered[[c for c in display_cols if c in df_filtered.columns]].copy()
    st.dataframe(disp_df, use_container_width=True, height=450)

    if os.path.exists("output/screener_output.xlsx"):
        with open("output/screener_output.xlsx", "rb") as f:
            st.download_button(
                "📥 Download Full screener_output.xlsx",
                f,
                file_name="screener_output.xlsx",
            )

# ----------------- TAB 2: Peer Comparison Engine -----------------
with main_tabs[1]:
    st.header("👥 Peer Percentile Rankings & Comparison")

    peer_df = get_peer_metrics_universe()
    peer_groups = sorted(peer_df["peer_group_name"].unique())

    selected_peer_group = st.selectbox("Choose Peer Group:", peer_groups)
    group_df = peer_df[peer_df["peer_group_name"] == selected_peer_group].copy()

    st.subheader(f"Peer Group: {selected_peer_group} ({len(group_df)} Companies)")

    bm_company = group_df[group_df["is_benchmark"] == 1]
    if not bm_company.empty:
        st.success(
            f"⭐ **Benchmark Company:** {bm_company.iloc[0]['company_name']} ({bm_company.iloc[0]['company_id']})"
        )

    # Display Peer Metrics Table
    show_cols = [
        "company_id",
        "company_name",
        "is_benchmark",
        "return_on_equity_pct",
        "roce_percentage",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
    ]
    st.dataframe(
        group_df[[c for c in show_cols if c in group_df.columns]],
        use_container_width=True,
    )

    # Plot Bar Comparison
    fig_peer = px.bar(
        group_df,
        x="company_id",
        y=["return_on_equity_pct", "roce_percentage", "net_profit_margin_pct"],
        barmode="group",
        title=f"Return & Margin Profiles across {selected_peer_group} Group",
    )
    st.plotly_chart(fig_peer, use_container_width=True)

    if os.path.exists("output/peer_comparison.xlsx"):
        with open("output/peer_comparison.xlsx", "rb") as f:
            st.download_button(
                "📥 Download Full peer_comparison.xlsx",
                f,
                file_name="peer_comparison.xlsx",
            )

# ----------------- TAB 3: Radar Charts -----------------
with main_tabs[2]:
    st.header("🕸️ Radar Analytics Charts")

    all_comps = query_db(
        "SELECT id, company_name FROM companies ORDER BY company_name;"
    )
    comp_map = {
        f"{row['company_name']} ({row['id']})": row["id"]
        for _, row in all_comps.iterrows()
    }

    selected_comp_label = st.selectbox(
        "Select Company for Radar Chart:", list(comp_map.keys())
    )
    cid = comp_map[selected_comp_label]

    radar_img_path = f"reports/radar_charts/{cid}_radar.png"
    if os.path.exists(radar_img_path):
        st.image(
            radar_img_path, caption=f"8-Axis Financial Radar Profile — {cid}", width=650
        )
    else:
        st.warning(
            f"Radar chart for {cid} not found at {radar_img_path}. Run `python -m src.analytics.radar` to generate."
        )

# ----------------- TAB 4: Single Company Deep Dive -----------------
with main_tabs[3]:
    st.header("📈 Single Company Financial Explorer")

    selected_company = st.selectbox(
        "Choose a company:", list(comp_map.keys()), key="deep_dive_comp"
    )
    selected_ticker = comp_map[selected_company]

    company_info = query_db(
        "SELECT * FROM companies WHERE id = ?;", (selected_ticker,)
    ).iloc[0]
    sector_info = query_db(
        "SELECT * FROM sectors WHERE company_id = ?;", (selected_ticker,)
    )
    pl_df = query_db(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year;",
        (selected_ticker,),
    )
    ratios_df = query_db(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year;",
        (selected_ticker,),
    )
    prices_df = query_db(
        "SELECT * FROM stock_prices WHERE company_id = ? ORDER BY date;",
        (selected_ticker,),
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"### {company_info['company_name']} ({selected_ticker})")
        if not sector_info.empty:
            sec = sector_info.iloc[0]
            st.markdown(
                f"**Broad Sector:** {sec['broad_sector']} | **Sub-Sector:** {sec['sub_sector']}"
            )
        st.write(company_info["about_company"])

    with c2:
        st.markdown(
            f"""
        <div class="metric-card">
            <p><b>ROCE:</b> {company_info['roce_percentage']}%</p>
            <p><b>ROE:</b> {company_info['roe_percentage']}%</p>
            <p><b>Book Value:</b> ₹{company_info['book_value']}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if not prices_df.empty:
        fig_price = px.line(
            prices_df,
            x="date",
            y="close_price",
            title=f"{selected_ticker} Stock Price Trend",
        )
        st.plotly_chart(fig_price, use_container_width=True)
