import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time

import pandas as pd

from src.dashboard.utils.db import (
    get_bs,
    get_cf,
    get_companies,
    get_peers,
    get_pl,
    get_pros_cons,
    get_ratios,
    get_sectors,
    get_valuation,
)


def test_db_cached_functions():
    """Verify cached db query functions return valid DataFrames."""
    comps = get_companies()
    assert not comps.empty
    assert len(comps) == 92

    sectors = get_sectors()
    assert not sectors.empty

    peers = get_peers()
    assert not peers.empty


def test_tickers_across_sectors():
    """Test 10 representative tickers across IT, Financials, FMCG, Energy, Healthcare."""
    test_tickers = [
        "TCS",
        "INFY",
        "HDFCBANK",
        "ICICIBANK",
        "HINDUNILVR",
        "ITC",
        "RELIANCE",
        "TATAMOTORS",
        "SUNPHARMA",
        "LT",
    ]

    for ticker in test_tickers:
        start_time = time.time()

        ratios = get_ratios(ticker=ticker)
        pl = get_pl(ticker=ticker)
        bs = get_bs(ticker=ticker)
        cf = get_cf(ticker=ticker)
        val = get_valuation(ticker=ticker)
        pc = get_pros_cons(ticker=ticker)

        elapsed = time.time() - start_time
        assert (
            elapsed < 3.0
        ), f"Company Profile data load for {ticker} took {elapsed:.2f}s (exceeded 3s target)"


def test_partial_data_tickers():
    """Verify tickers with partial historical data do not raise exceptions."""
    comps = get_companies()
    for _, row in comps.iterrows():
        ticker = row["id"]
        pl = get_pl(ticker=ticker)
        ratios = get_ratios(ticker=ticker)
        if not pl.empty and "sales" in pl.columns:
            _ = pl["sales"].dropna().mean()
        if not ratios.empty and "return_on_equity_pct" in ratios.columns:
            _ = ratios["return_on_equity_pct"].dropna().median()


def test_screener_extreme_sliders():
    """Verify screener filtering logic with extreme slider boundaries."""
    comps = get_companies()
    ratios = get_ratios()
    val = get_valuation()

    ratios_latest = (
        ratios.sort_values("year").groupby("company_id").last().reset_index()
    )
    val_latest = val.sort_values("year").groupby("company_id").last().reset_index()

    merged = pd.merge(
        comps, ratios_latest, left_on="id", right_on="company_id", how="inner"
    )
    merged = pd.merge(
        merged,
        val_latest[["company_id", "pe_ratio", "pb_ratio"]],
        on="company_id",
        how="left",
    )

    # Extreme low
    mask_min = (merged["return_on_equity_pct"].fillna(-999) >= -100) & (
        merged["debt_to_equity"].fillna(999) <= 0.0
    )
    res_min = merged[mask_min]
    assert isinstance(res_min, pd.DataFrame)

    # Extreme high
    mask_max = (merged["return_on_equity_pct"].fillna(-999) >= 100) & (
        merged["debt_to_equity"].fillna(999) <= 100.0
    )
    res_max = merged[mask_max]
    assert isinstance(res_max, pd.DataFrame)


def test_valuation_deliverables_exist():
    """Verify valuation output files exist and match specifications."""
    assert os.path.exists("output/valuation_summary.xlsx")
    assert os.path.exists("output/valuation_flags.csv")

    summary = pd.read_excel("output/valuation_summary.xlsx")
    assert len(summary) == 92
    assert "FCF_yield_pct" in summary.columns
    assert "PE_vs_sector_median_pct" in summary.columns
    assert "flag" in summary.columns

    flags = pd.read_csv("output/valuation_flags.csv")
    assert set(flags["flag"].unique()).issubset({"Caution", "Discount"})


if __name__ == "__main__":
    test_db_cached_functions()
    test_tickers_across_sectors()
    test_partial_data_tickers()
    test_screener_extreme_sliders()
    test_valuation_deliverables_exist()
    print("ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
