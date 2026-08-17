import os
import sqlite3

import numpy as np
import pandas as pd


def run_valuation_analysis(db_path: str = "nifty100.db", output_dir: str = "output"):
    """
    Computes valuation metrics including FCF yield, sector median P/E comparisons,
    and overvaluation/discount flags for all 92 companies.
    Generates output/valuation_summary.xlsx and output/valuation_flags.csv.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        # Load 2024 market cap data
        mc_2024 = pd.read_sql(
            "SELECT company_id, year, market_cap_crore, pe_ratio, pb_ratio, ev_ebitda FROM market_cap WHERE year=2024",
            conn,
        )

        # Load historical market cap data (2019-2024) for 5yr median PE
        mc_hist = pd.read_sql(
            "SELECT company_id, year, pe_ratio FROM market_cap WHERE year>=2019 AND year<=2024",
            conn,
        )

        # Load companies metadata and sector mapping
        comps = pd.read_sql(
            """
            SELECT c.id as company_id, c.company_name, s.broad_sector as sector
            FROM companies c
            LEFT JOIN sectors s ON c.id = s.company_id
            ORDER BY c.id
        """,
            conn,
        )

        # Load 2024 financial ratios for Free Cash Flow
        ratios_2024 = pd.read_sql(
            "SELECT company_id, year, free_cash_flow_cr FROM financial_ratios WHERE year=2024",
            conn,
        )
    finally:
        conn.close()

    # Merge datasets
    df = pd.merge(comps, mc_2024, on="company_id", how="left")
    df = pd.merge(
        df,
        ratios_2024[["company_id", "free_cash_flow_cr"]],
        on="company_id",
        how="left",
    )

    # 1. Compute FCF yield (%): (FCF / market_cap_crore) * 100
    df["FCF_yield_pct"] = np.where(
        (df["market_cap_crore"].notna()) & (df["market_cap_crore"] > 0),
        (df["free_cash_flow_cr"] / df["market_cap_crore"]) * 100.0,
        np.nan,
    )

    # 2. Compute 5-year median PE per company
    median_5yr = (
        mc_hist.groupby("company_id")["pe_ratio"]
        .apply(lambda s: s.dropna().median())
        .reset_index()
    )
    median_5yr.columns = ["company_id", "5yr_median_PE"]
    df = pd.merge(df, median_5yr, on="company_id", how="left")

    # 3. Compute sector median P/E (2024)
    sector_medians = (
        df.groupby("sector")["pe_ratio"]
        .apply(lambda s: s.dropna().median())
        .reset_index()
    )
    sector_medians.columns = ["sector", "sector_median_PE"]
    df = pd.merge(df, sector_medians, on="sector", how="left")

    # 4. Compute PE vs sector median (%)
    df["PE_vs_sector_median_pct"] = np.where(
        (df["sector_median_PE"].notna())
        & (df["sector_median_PE"] > 0)
        & (df["pe_ratio"].notna()),
        ((df["pe_ratio"] - df["sector_median_PE"]) / df["sector_median_PE"]) * 100.0,
        np.nan,
    )

    # 5. Apply overvaluation flags
    def assign_flag(row):
        pe = row["pe_ratio"]
        sec_pe = row["sector_median_PE"]
        if pd.isna(pe) or pd.isna(sec_pe):
            return "Fair"
        if pe > sec_pe * 1.5:
            return "Caution"
        elif pe < sec_pe * 0.7:
            return "Discount"
        else:
            return "Fair"

    df["flag"] = df.apply(assign_flag, axis=1)

    # Format and select columns for valuation_summary.xlsx
    summary_columns = {
        "company_id": "company_id",
        "company_name": "company_name",
        "sector": "sector",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "ev_ebitda": "EV/EBITDA",
        "FCF_yield_pct": "FCF_yield_pct",
        "5yr_median_PE": "5yr_median_PE",
        "PE_vs_sector_median_pct": "PE_vs_sector_median_pct",
        "flag": "flag",
    }

    summary_df = df[list(summary_columns.keys())].rename(columns=summary_columns)

    # Export valuation_summary.xlsx
    xlsx_path = os.path.join(output_dir, "valuation_summary.xlsx")
    summary_df.to_excel(xlsx_path, index=False)
    print(f"Saved valuation summary with {len(summary_df)} companies to: {xlsx_path}")

    # Generate valuation_flags.csv: only Caution and Discount companies
    flags_df = summary_df[summary_df["flag"].isin(["Caution", "Discount"])].copy()
    csv_path = os.path.join(output_dir, "valuation_flags.csv")
    flags_df.to_csv(csv_path, index=False)
    print(f"Saved valuation flags ({len(flags_df)} companies) to: {csv_path}")


if __name__ == "__main__":
    run_valuation_analysis()
