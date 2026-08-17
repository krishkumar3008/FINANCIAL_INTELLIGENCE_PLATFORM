import os
import sqlite3

import pandas as pd
import streamlit as st


def get_db_path() -> str:
    """Resolve nifty100.db absolute path."""
    root_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    db_file = os.path.join(root_dir, "nifty100.db")
    if os.path.exists(db_file):
        return db_file
    return "nifty100.db"


def query_db_df(query: str, params: tuple = ()) -> pd.DataFrame:
    """Execute SQL query and return pandas DataFrame."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Retrieve all companies with sector information."""
    query = """
    SELECT c.id, c.company_name, c.company_logo, c.chart_link, c.about_company,
           c.website, c.nse_profile, c.bse_profile, c.face_value, c.book_value,
           c.roce_percentage, c.roe_percentage,
           s.broad_sector, s.sub_sector, s.index_weight_pct, s.market_cap_category
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    ORDER BY c.company_name;
    """
    return query_db_df(query)


@st.cache_data(ttl=600)
def get_ratios(ticker: str = None, year: int = None) -> pd.DataFrame:
    """Retrieve financial ratios with optional filtering."""
    query = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker.upper())
    if year is not None:
        query += " AND year = ?"
        params.append(int(year))
    query += " ORDER BY company_id, year;"
    return query_db_df(query, tuple(params))


@st.cache_data(ttl=600)
def get_pl(ticker: str = None) -> pd.DataFrame:
    """Retrieve profit and loss statement records."""
    query = "SELECT * FROM profitandloss WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker.upper())
    query += " ORDER BY company_id, year;"
    return query_db_df(query, tuple(params))


@st.cache_data(ttl=600)
def get_bs(ticker: str = None) -> pd.DataFrame:
    """Retrieve balance sheet records."""
    query = "SELECT * FROM balancesheet WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker.upper())
    query += " ORDER BY company_id, year;"
    return query_db_df(query, tuple(params))


@st.cache_data(ttl=600)
def get_cf(ticker: str = None) -> pd.DataFrame:
    """Retrieve cash flow statement records."""
    query = "SELECT * FROM cashflow WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker.upper())
    query += " ORDER BY company_id, year;"
    return query_db_df(query, tuple(params))


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Retrieve sector mapping information."""
    query = "SELECT * FROM sectors ORDER BY broad_sector, sub_sector;"
    return query_db_df(query)


@st.cache_data(ttl=600)
def get_peers(group_name: str = None) -> pd.DataFrame:
    """Retrieve peer group records."""
    query = """
    SELECT pg.*, c.company_name, s.broad_sector
    FROM peer_groups pg
    JOIN companies c ON pg.company_id = c.id
    LEFT JOIN sectors s ON c.id = s.company_id
    WHERE 1=1
    """
    params = []
    if group_name:
        query += " AND pg.peer_group_name = ?"
        params.append(group_name)
    query += " ORDER BY pg.peer_group_name, c.company_name;"
    return query_db_df(query, tuple(params))


@st.cache_data(ttl=600)
def get_valuation(ticker: str = None) -> pd.DataFrame:
    """Retrieve valuation and market cap data."""
    query = """
    SELECT m.*, c.company_name, s.broad_sector
    FROM market_cap m
    JOIN companies c ON m.company_id = c.id
    LEFT JOIN sectors s ON c.id = s.company_id
    WHERE 1=1
    """
    params = []
    if ticker:
        query += " AND m.company_id = ?"
        params.append(ticker.upper())
    query += " ORDER BY m.company_id, m.year;"
    return query_db_df(query, tuple(params))


@st.cache_data(ttl=600)
def get_documents(ticker: str = None) -> pd.DataFrame:
    """Retrieve annual report document links."""
    query = "SELECT * FROM documents WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker.upper())
    query += " ORDER BY company_id, year DESC;"
    return query_db_df(query, tuple(params))


@st.cache_data(ttl=600)
def get_pros_cons(ticker: str = None) -> pd.DataFrame:
    """Retrieve company pros and cons text."""
    query = "SELECT * FROM prosandcons WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker.upper())
    return query_db_df(query, tuple(params))


@st.cache_data(ttl=600)
def get_capital_allocation() -> pd.DataFrame:
    """Retrieve capital allocation patterns output dataset."""
    root_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    cap_file = os.path.join(root_dir, "output", "capital_allocation.csv")
    if os.path.exists(cap_file):
        return pd.read_csv(cap_file)
    return pd.DataFrame()
