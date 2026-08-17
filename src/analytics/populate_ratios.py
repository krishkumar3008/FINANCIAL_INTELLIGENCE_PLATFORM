import os

import pandas as pd

from src.analytics.cagr import compute_cagr
from src.analytics.cashflow_kpis import (
    classify_capital_allocation,
    compute_capex_intensity,
    compute_cfo_quality_score,
    compute_fcf_conversion_rate,
    compute_free_cash_flow,
)
from src.analytics.ratios import (
    compute_asset_turnover,
    compute_debt_to_equity,
    compute_interest_coverage,
    compute_net_profit_margin,
    compute_operating_profit_margin,
    compute_return_on_capital_employed,
    compute_return_on_equity,
    get_icr_label,
    is_high_leverage,
    is_icr_at_risk,
)
from src.database import get_db_connection, init_db


def run_ratio_engine(db_path: str = "nifty100.db") -> None:
    print("Re-initializing database schema for financial_ratios table...")
    conn = get_db_connection(db_path)
    try:
        # Recreate the financial_ratios table to apply the updated schema
        conn.execute("DROP TABLE IF EXISTS financial_ratios;")
        conn.commit()
    finally:
        conn.close()

    # Initialize DB (executes schema.sql)
    init_db(db_path, "db/schema.sql")

    # Establish connection to load data
    conn = get_db_connection(db_path)

    try:
        # 1. Fetch companies, sectors, P&L, balance sheet, and cash flow data
        companies = conn.execute(
            "SELECT id, roce_percentage, roe_percentage FROM companies"
        ).fetchall()
        sectors = conn.execute(
            "SELECT company_id, broad_sector FROM sectors"
        ).fetchall()
        pl_rows = conn.execute("SELECT * FROM profitandloss").fetchall()
        bs_rows = conn.execute("SELECT * FROM balancesheet").fetchall()
        cf_rows = conn.execute("SELECT * FROM cashflow").fetchall()

        # 2. Build lookups
        company_sectors = {row["company_id"]: row["broad_sector"] for row in sectors}
        company_pre_ratios = {
            row["id"]: (row["roce_percentage"], row["roe_percentage"])
            for row in companies
        }

        # Group P&L, BS, CF records by company and year
        pl_by_company: dict[str, dict[int, dict]] = {}
        for row in pl_rows:
            comp_id = row["company_id"]
            year = row["year"]
            if comp_id not in pl_by_company:
                pl_by_company[comp_id] = {}
            pl_by_company[comp_id][year] = dict(row)

        bs_by_company: dict[str, dict[int, dict]] = {}
        for row in bs_rows:
            comp_id = row["company_id"]
            year = row["year"]
            if comp_id not in bs_by_company:
                bs_by_company[comp_id] = {}
            bs_by_company[comp_id][year] = dict(row)

        cf_by_company: dict[str, dict[int, dict]] = {}
        for row in cf_rows:
            comp_id = row["company_id"]
            year = row["year"]
            if comp_id not in cf_by_company:
                cf_by_company[comp_id] = {}
            cf_by_company[comp_id][year] = dict(row)

        ratio_records = []
        cap_alloc_records = []

        # Create output directory and clear log
        os.makedirs("output", exist_ok=True)
        if os.path.exists("output/ratio_edge_cases.log"):
            os.remove("output/ratio_edge_cases.log")

        print("Calculating KPIs for all companies...")

        for comp in companies:
            comp_id = comp["id"]
            sector = company_sectors.get(comp_id, "Unknown")
            pre_roce, pre_roe = company_pre_ratios.get(comp_id, (None, None))

            comp_pl = pl_by_company.get(comp_id, {})
            comp_bs = bs_by_company.get(comp_id, {})
            comp_cf = cf_by_company.get(comp_id, {})

            # Sorted list of normal years for CAGR lookups
            sorted_years = sorted([y for y in comp_pl.keys() if y != 9999])

            # Store calculated ratios for ROCE/ROE cross-check (latest year)
            latest_computed_roce = None
            latest_computed_roe = None
            latest_year_for_crosscheck = None

            for year, pl in comp_pl.items():
                bs = comp_bs.get(year, {})
                cf = comp_cf.get(year, {})

                # Fetch inputs from P&L
                sales = pl.get("sales", 0.0) or 0.0
                operating_profit = pl.get("operating_profit", 0.0) or 0.0
                reported_opm = pl.get("opm_percentage")
                other_income = pl.get("other_income", 0.0) or 0.0
                interest = pl.get("interest", 0.0) or 0.0
                profit_before_tax = pl.get("profit_before_tax", 0.0) or 0.0
                net_profit = pl.get("net_profit", 0.0) or 0.0
                eps = pl.get("eps", 0.0) or 0.0
                dividend_payout = pl.get("dividend_payout", 0.0) or 0.0

                # Fetch inputs from Balance Sheet (if available)
                equity_capital = bs.get("equity_capital", 0.0) or 0.0 if bs else 0.0
                reserves = bs.get("reserves", 0.0) or 0.0 if bs else 0.0
                borrowings = bs.get("borrowings", 0.0) or 0.0 if bs else 0.0
                total_assets = bs.get("total_assets", 0.0) or 0.0 if bs else 0.0
                investments = bs.get("investments", 0.0) or 0.0 if bs else 0.0

                # Fetch inputs from Cash Flow (if available)
                cfo = cf.get("operating_activity", 0.0) or 0.0 if cf else 0.0
                cfi = cf.get("investing_activity", 0.0) or 0.0 if cf else 0.0
                cff = cf.get("financing_activity", 0.0) or 0.0 if cf else 0.0

                # ----------------- Day 08 Profitability -----------------
                npm = compute_net_profit_margin(net_profit, sales)
                opm = compute_operating_profit_margin(
                    operating_profit, sales, reported_opm, comp_id, year
                )
                roe = (
                    compute_return_on_equity(net_profit, equity_capital, reserves)
                    if bs
                    else None
                )
                roce = (
                    compute_return_on_capital_employed(
                        profit_before_tax,
                        interest,
                        equity_capital,
                        reserves,
                        borrowings,
                    )
                    if bs
                    else None
                )

                # Record latest non-TTM ROCE/ROE for cross-checking
                if year != 9999 and bs:
                    if (
                        latest_year_for_crosscheck is None
                        or year > latest_year_for_crosscheck
                    ):
                        latest_year_for_crosscheck = year
                        latest_computed_roce = roce
                        latest_computed_roe = roe

                # ----------------- Day 09 Leverage & Efficiency -----------------
                de = (
                    compute_debt_to_equity(borrowings, equity_capital, reserves)
                    if bs
                    else None
                )
                high_lev = is_high_leverage(de, sector) if bs else False
                icr = compute_interest_coverage(
                    operating_profit, other_income, interest
                )
                icr_lbl = get_icr_label(interest)
                icr_warning = is_icr_at_risk(icr)
                asset_turn = compute_asset_turnover(sales, total_assets) if bs else None

                # ----------------- Day 11 Cash Flow KPIs -----------------
                fcf = compute_free_cash_flow(cfo, cfi) if cf else None
                capex_val = abs(cfi) if cf else 0.0
                _, capex_intensity_lbl = (
                    compute_capex_intensity(cfi, sales)
                    if (cf and sales)
                    else (None, None)
                )
                fcf_conv = (
                    compute_fcf_conversion_rate(fcf, operating_profit)
                    if (cf and fcf is not None)
                    else None
                )

                # 5-year average CFO/PAT for CFO Quality
                # We need the ratios list for years Y-4 to Y
                cfo_pat_ratios = []
                cfo_pat_valid = True
                if year != 9999:
                    for t in range(year - 4, year + 1):
                        t_pl = comp_pl.get(t)
                        t_cf = comp_cf.get(t)
                        if not t_pl or not t_cf:
                            cfo_pat_valid = False
                            break
                        t_pat = t_pl.get("net_profit", 0.0) or 0.0
                        t_cfo = t_cf.get("operating_activity", 0.0) or 0.0
                        if t_pat == 0:
                            cfo_pat_valid = False
                            break
                        cfo_pat_ratios.append(t_cfo / t_pat)
                else:
                    cfo_pat_valid = False

                cfo_pat_avg, quality_score = (
                    compute_cfo_quality_score(cfo_pat_ratios)
                    if cfo_pat_valid
                    else (None, None)
                )

                # Capital allocation pattern
                pattern_lbl = (
                    classify_capital_allocation(cfo, cfi, cff, cfo_pat_avg)
                    if cf
                    else "Mixed"
                )
                if cf:
                    cfo_sign = "+" if cfo >= 0 else "-"
                    cfi_sign = "+" if cfi >= 0 else "-"
                    cff_sign = "+" if cff >= 0 else "-"
                    cap_alloc_records.append(
                        {
                            "company_id": comp_id,
                            "year": year,
                            "cfo_sign": cfo_sign,
                            "cfi_sign": cfi_sign,
                            "cff_sign": cff_sign,
                            "pattern_label": pattern_lbl,
                        }
                    )

                # ----------------- Day 10 CAGR -----------------
                rev_cagr_5, rev_cagr_5_flag = (None, "INSUFFICIENT")
                pat_cagr_5, pat_cagr_5_flag = (None, "INSUFFICIENT")
                eps_cagr_5, eps_cagr_5_flag = (None, "INSUFFICIENT")

                if year != 9999:
                    start_yr = year - 5
                    if start_yr in comp_pl:
                        rev_cagr_5, rev_cagr_5_flag = compute_cagr(
                            comp_pl[start_yr].get("sales"), sales, 5
                        )
                        pat_cagr_5, pat_cagr_5_flag = compute_cagr(
                            comp_pl[start_yr].get("net_profit"), net_profit, 5
                        )
                        eps_cagr_5, eps_cagr_5_flag = compute_cagr(
                            comp_pl[start_yr].get("eps"), eps, 5
                        )

                # BVPS
                bvps = (
                    ((equity_capital + reserves) / (10 * equity_capital))
                    if (bs and equity_capital != 0)
                    else None
                )

                record = {
                    "company_id": comp_id,
                    "year": year,
                    "net_profit_margin_pct": npm,
                    "operating_profit_margin_pct": opm,
                    "return_on_equity_pct": roe,
                    "debt_to_equity": de,
                    "high_leverage_flag": 1 if high_lev else 0,
                    "interest_coverage": icr,
                    "icr_label": icr_lbl,
                    "icr_warning_flag": 1 if icr_warning else 0,
                    "asset_turnover": asset_turn,
                    "free_cash_flow_cr": fcf,
                    "capex_cr": capex_val if bs else None,
                    "earnings_per_share": eps,
                    "book_value_per_share": bvps,
                    "dividend_payout_ratio_pct": dividend_payout,
                    "total_debt_cr": borrowings if bs else None,
                    "cash_from_operations_cr": cfo if cf else None,
                    "revenue_cagr_5yr": rev_cagr_5,
                    "revenue_cagr_5yr_flag": rev_cagr_5_flag,
                    "pat_cagr_5yr": pat_cagr_5,
                    "pat_cagr_5yr_flag": pat_cagr_5_flag,
                    "eps_cagr_5yr": eps_cagr_5,
                    "eps_cagr_5yr_flag": eps_cagr_5_flag,
                    "composite_quality_score": quality_score,
                }
                ratio_records.append(record)

            # Perform Cross-check of latest computed ROCE and ROE against companies.xlsx values (from companies table)
            if latest_year_for_crosscheck is not None:
                # ROCE crosscheck
                if latest_computed_roce is not None and pre_roce is not None:
                    diff_roce = abs(latest_computed_roce - pre_roce)
                    if diff_roce > 5.0:
                        # Categorise
                        category = "data source issue"
                        if sector == "Financials":
                            category = "formula discrepancy"
                        elif comp_id in ["GODREJCP"]:
                            category = "version difference"

                        msg = f"[ROCE_ANOMALY] {comp_id} (Year {latest_year_for_crosscheck}): computed ROCE={latest_computed_roce:.2f}%, pre-computed ROCE={pre_roce}%, diff={diff_roce:.2f}% | Category: {category}"
                        with open(
                            "output/ratio_edge_cases.log", "a", encoding="utf-8"
                        ) as f:
                            f.write(msg + "\n")

                # ROE crosscheck
                if latest_computed_roe is not None and pre_roe is not None:
                    diff_roe = abs(latest_computed_roe - pre_roe)
                    if diff_roe > 5.0:
                        # Categorise
                        category = "data source issue"
                        if comp_id == "TCS":
                            category = "data source issue (scaling)"
                        elif comp_id in ["GODREJCP"]:
                            category = "version difference"
                        elif sector == "Financials":
                            category = "formula discrepancy"

                        msg = f"[ROE_ANOMALY] {comp_id} (Year {latest_year_for_crosscheck}): computed ROE={latest_computed_roe:.2f}%, pre-computed ROE={pre_roe}%, diff={diff_roe:.2f}% | Category: {category}"
                        with open(
                            "output/ratio_edge_cases.log", "a", encoding="utf-8"
                        ) as f:
                            f.write(msg + "\n")

        # 3. Write all records into SQLite database table 'financial_ratios'
        df_ratios = pd.DataFrame(ratio_records)
        df_ratios.to_sql("financial_ratios", conn, if_exists="append", index=False)
        print(f"Successfully loaded {len(df_ratios)} rows to 'financial_ratios' table.")

        # 4. Generate capital allocation CSV
        df_cap_alloc = pd.DataFrame(cap_alloc_records)
        df_cap_alloc.to_csv("output/capital_allocation.csv", index=False)
        print(
            f"Successfully generated capital allocation CSV with {len(df_cap_alloc)} rows."
        )

    except Exception as e:
        conn.rollback()
        print(f"Error during ratio calculation and loading: {e}")
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    run_ratio_engine()
