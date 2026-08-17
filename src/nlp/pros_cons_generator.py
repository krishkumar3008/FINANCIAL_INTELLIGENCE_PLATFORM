import os
import sqlite3

import pandas as pd


def generate_pros_and_cons(
    db_path: str = "nifty100.db", output_path: str = "output/pros_cons_generated.csv"
) -> pd.DataFrame:
    """
    Generates Pros and Cons for all 92 companies based on financial analysis rules.
    Assigns confidence score (0-100%) and filters output to confidence > 60%.
    Ensures every company has at least 1 pro and at least 1 con.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Fetch companies and sectors
    companies = pd.read_sql("SELECT * FROM companies", conn).to_dict("records")
    sectors_df = pd.read_sql(
        "SELECT company_id, broad_sector, sub_sector FROM sectors", conn
    )
    sector_map = {r["company_id"]: r["broad_sector"] for _, r in sectors_df.iterrows()}

    # Fetch financial data grouped by company
    pnl_df = pd.read_sql("SELECT * FROM profitandloss ORDER BY year ASC", conn)
    bs_df = pd.read_sql("SELECT * FROM balancesheet ORDER BY year ASC", conn)
    cf_df = pd.read_sql("SELECT * FROM cashflow ORDER BY year ASC", conn)
    ratios_df = pd.read_sql("SELECT * FROM financial_ratios ORDER BY year ASC", conn)
    mcap_df = pd.read_sql("SELECT * FROM market_cap ORDER BY year ASC", conn)

    conn.close()

    results = []

    financial_sector_keywords = [
        "financial",
        "banking",
        "bank",
        "nbfc",
        "finance",
        "insurance",
    ]

    for comp in companies:
        comp_id = comp["id"]
        broad_sec = sector_map.get(comp_id, "").lower()
        is_financial = any(k in broad_sec for k in financial_sector_keywords)

        comp_pnl = pnl_df[pnl_df["company_id"] == comp_id].sort_values("year")
        comp_bs = bs_df[bs_df["company_id"] == comp_id].sort_values("year")
        comp_cf = cf_df[cf_df["company_id"] == comp_id].sort_values("year")
        comp_ratios = ratios_df[ratios_df["company_id"] == comp_id].sort_values("year")
        comp_mcap = mcap_df[mcap_df["company_id"] == comp_id].sort_values("year")

        pros = []
        cons = []

        # Latest year ratios
        latest_ratio = comp_ratios.iloc[-1] if not comp_ratios.empty else {}
        latest_pnl = comp_pnl.iloc[-1] if not comp_pnl.empty else {}
        latest_bs = comp_bs.iloc[-1] if not comp_bs.empty else {}
        latest_cf = comp_cf.iloc[-1] if not comp_cf.empty else {}
        latest_mcap = comp_mcap.iloc[-1] if not comp_mcap.empty else {}

        # Metric series
        roe_series = (
            comp_ratios["return_on_equity_pct"].dropna().tolist()
            if "return_on_equity_pct" in comp_ratios
            else []
        )
        if not roe_series and "roe_percentage" in comp:
            if comp["roe_percentage"] is not None:
                roe_series = [comp["roe_percentage"]]

        opm_series = (
            comp_pnl["opm_percentage"].dropna().tolist()
            if "opm_percentage" in comp_pnl
            else []
        )
        sales_series = (
            comp_pnl["sales"].dropna().tolist() if "sales" in comp_pnl else []
        )
        pat_series = (
            comp_pnl["net_profit"].dropna().tolist() if "net_profit" in comp_pnl else []
        )
        eps_series = comp_pnl["eps"].dropna().tolist() if "eps" in comp_pnl else []
        de_series = (
            comp_ratios["debt_to_equity"].dropna().tolist()
            if "debt_to_equity" in comp_ratios
            else []
        )
        fcf_series = (
            comp_ratios["free_cash_flow_cr"].dropna().tolist()
            if "free_cash_flow_cr" in comp_ratios
            else []
        )
        icr = latest_ratio.get("interest_coverage", None)

        rev_cagr_5 = latest_ratio.get("revenue_cagr_5yr", None)
        pat_cagr_5 = latest_ratio.get("pat_cagr_5yr", None)
        eps_cagr_5 = latest_ratio.get("eps_cagr_5yr", None)
        div_yield = latest_mcap.get("dividend_yield_pct", 0) or 0
        div_payout = latest_pnl.get("dividend_payout", 0) or 0
        latest_de = latest_ratio.get("debt_to_equity", 0) or 0
        latest_opm = latest_pnl.get("opm_percentage", 0) or 0
        latest_pat = latest_pnl.get("net_profit", 0) or 0

        # --- PRO RULES ---

        # Pro Rule 1: ROE > 20% sustained for 3+ years
        if len(roe_series) >= 3 and all(r > 20.0 for r in roe_series[-3:]):
            pros.append(
                {
                    "rule_id": "PRO_01",
                    "text": "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
                    "confidence_pct": 95,
                }
            )

        # Pro Rule 2: FCF positive for 5+ consecutive years
        if len(fcf_series) >= 5 and all(f > 0 for f in fcf_series[-5:]):
            pros.append(
                {
                    "rule_id": "PRO_02",
                    "text": "Strong free cash flow generation over 5 years signals healthy business fundamentals",
                    "confidence_pct": 90,
                }
            )
        elif len(fcf_series) >= 3 and all(f > 0 for f in fcf_series[-3:]):
            pros.append(
                {
                    "rule_id": "PRO_02_SUB",
                    "text": "Strong free cash flow generation over recent years signals healthy business fundamentals",
                    "confidence_pct": 80,
                }
            )

        # Pro Rule 3: D/E = 0 in latest year
        if latest_de == 0 or (latest_bs.get("borrowings", 0) or 0) == 0:
            pros.append(
                {
                    "rule_id": "PRO_03",
                    "text": "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
                    "confidence_pct": 95,
                }
            )

        # Pro Rule 4: Revenue CAGR > 15% over 5 years
        if rev_cagr_5 is not None and rev_cagr_5 > 15.0:
            pros.append(
                {
                    "rule_id": "PRO_04",
                    "text": "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
                    "confidence_pct": 90,
                }
            )

        # Pro Rule 5: OPM > 25% in latest year
        if latest_opm > 25.0:
            pros.append(
                {
                    "rule_id": "PRO_05",
                    "text": "Operating profit margin above 25% indicates strong pricing power and cost discipline",
                    "confidence_pct": 85,
                }
            )

        # Pro Rule 6: PAT CAGR > 20% over 5 years
        if pat_cagr_5 is not None and pat_cagr_5 > 20.0:
            pros.append(
                {
                    "rule_id": "PRO_06",
                    "text": "Net profit compounding at above 20% over 5 years creates significant shareholder value",
                    "confidence_pct": 90,
                }
            )

        # Pro Rule 7: ICR > 10 or Debt Free
        if (icr is not None and icr > 10.0) or latest_de == 0:
            pros.append(
                {
                    "rule_id": "PRO_07",
                    "text": "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                    "confidence_pct": 90,
                }
            )

        # Pro Rule 8: Dividend Yield > 2% with FCF positive
        latest_fcf = fcf_series[-1] if fcf_series else 0
        if div_yield > 2.0 and latest_fcf > 0:
            pros.append(
                {
                    "rule_id": "PRO_08",
                    "text": "Consistent dividend yield above 2% backed by positive free cash flow",
                    "confidence_pct": 85,
                }
            )

        # Pro Rule 9: EPS CAGR > 15% over 5 years
        if eps_cagr_5 is not None and eps_cagr_5 > 15.0:
            pros.append(
                {
                    "rule_id": "PRO_09",
                    "text": "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
                    "confidence_pct": 90,
                }
            )

        # Pro Rule 10: ROE improving for 3 consecutive years
        if len(roe_series) >= 3 and roe_series[-1] > roe_series[-2] > roe_series[-3]:
            pros.append(
                {
                    "rule_id": "PRO_10",
                    "text": "Return on equity improving for 3 consecutive years shows strengthening business quality",
                    "confidence_pct": 85,
                }
            )

        # Pro Rule 11: Revenue CAGR > PAT CAGR (or PAT compounding faster than revenue -> improving operating leverage)
        if pat_cagr_5 is not None and rev_cagr_5 is not None:
            if pat_cagr_5 > rev_cagr_5 and pat_cagr_5 > 5.0:
                pros.append(
                    {
                        "rule_id": "PRO_11",
                        "text": "Revenue growing slower than profits shows improving operating leverage and scale benefits",
                        "confidence_pct": 85,
                    }
                )

        # Pro Rule 12: Balance sheet assets growing with declining debt
        assets_series = (
            comp_bs["total_assets"].dropna().tolist()
            if "total_assets" in comp_bs
            else []
        )
        borrow_series = (
            comp_bs["borrowings"].dropna().tolist() if "borrowings" in comp_bs else []
        )
        if len(assets_series) >= 3 and len(borrow_series) >= 3:
            if (
                assets_series[-1] > assets_series[-3]
                and borrow_series[-1] < borrow_series[-3]
            ):
                pros.append(
                    {
                        "rule_id": "PRO_12",
                        "text": "Growing asset base funded by internal accruals reflects self-sustaining growth",
                        "confidence_pct": 85,
                    }
                )

        # Fallback Pro if none matched
        if not pros:
            roce_val = (
                comp.get("roce_percentage")
                or latest_ratio.get("roce_percentage")
                or 15.0
            )
            if roce_val > 12.0:
                pros.append(
                    {
                        "rule_id": "PRO_FALLBACK_ROCE",
                        "text": "Healthy return on capital employed demonstrates steady business profitability",
                        "confidence_pct": 75,
                    }
                )
            elif latest_pat > 0:
                pros.append(
                    {
                        "rule_id": "PRO_FALLBACK_PAT",
                        "text": "Consistently profitable operation generates baseline positive earnings",
                        "confidence_pct": 70,
                    }
                )
            else:
                pros.append(
                    {
                        "rule_id": "PRO_FALLBACK_GEN",
                        "text": "Established market presence within the Nifty 100 benchmark index",
                        "confidence_pct": 65,
                    }
                )

        # --- CON RULES ---

        # Con Rule 1: D/E > 2.0 for non-financial companies
        if not is_financial and latest_de > 2.0:
            pros_text_de = f"Debt-to-equity ratio of {latest_de:.2f} is elevated for a non-financial company and warrants monitoring"
            cons.append(
                {"rule_id": "CON_01", "text": pros_text_de, "confidence_pct": 90}
            )

        # Con Rule 2: FCF negative for 3 consecutive years
        if len(fcf_series) >= 3 and all(f < 0 for f in fcf_series[-3:]):
            cons.append(
                {
                    "rule_id": "CON_02",
                    "text": "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
                    "confidence_pct": 90,
                }
            )

        # Con Rule 3: OPM declining for 3 consecutive years
        if len(opm_series) >= 3 and opm_series[-1] < opm_series[-2] < opm_series[-3]:
            cons.append(
                {
                    "rule_id": "CON_03",
                    "text": "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
                    "confidence_pct": 85,
                }
            )

        # Con Rule 4: Net profit negative in latest year
        if latest_pat < 0:
            cons.append(
                {
                    "rule_id": "CON_04",
                    "text": "Company reported a net loss in the most recent financial year",
                    "confidence_pct": 95,
                }
            )

        # Con Rule 5: Revenue declining for 2+ years
        if (
            len(sales_series) >= 3
            and sales_series[-1] < sales_series[-2] < sales_series[-3]
        ):
            cons.append(
                {
                    "rule_id": "CON_05",
                    "text": "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
                    "confidence_pct": 90,
                }
            )

        # Con Rule 6: ICR < 1.5
        if icr is not None and icr < 1.5 and latest_de > 0.1:
            cons.append(
                {
                    "rule_id": "CON_06",
                    "text": "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
                    "confidence_pct": 90,
                }
            )

        # Con Rule 7: Dividend payout > 100%
        if div_payout > 100.0:
            cons.append(
                {
                    "rule_id": "CON_07",
                    "text": "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
                    "confidence_pct": 85,
                }
            )

        # Con Rule 8: D/E rising for 3 consecutive years
        if len(de_series) >= 3 and de_series[-1] > de_series[-2] > de_series[-3]:
            cons.append(
                {
                    "rule_id": "CON_08",
                    "text": "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
                    "confidence_pct": 85,
                }
            )

        # Con Rule 9: EPS declining for 3 consecutive years
        if len(eps_series) >= 3 and eps_series[-1] < eps_series[-2] < eps_series[-3]:
            cons.append(
                {
                    "rule_id": "CON_09",
                    "text": "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
                    "confidence_pct": 85,
                }
            )

        # Con Rule 10: ROCE < 10%
        roce_val = (
            comp.get("roce_percentage") or latest_ratio.get("roce_percentage") or 12.0
        )
        if roce_val < 10.0:
            cons.append(
                {
                    "rule_id": "CON_10",
                    "text": "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
                    "confidence_pct": 85,
                }
            )

        # Con Rule 11: Net Debt > 3x EBITDA
        borrowings = latest_bs.get("borrowings", 0) or 0
        cash = (latest_bs.get("other_asset", 0) or 0) * 0.2  # proxy or cash estimate
        net_debt = max(0, borrowings - cash)
        ebitda = (latest_pnl.get("operating_profit", 0) or 0) + (
            latest_pnl.get("other_income", 0) or 0
        )
        if ebitda > 0 and (net_debt / ebitda) > 3.0:
            cons.append(
                {
                    "rule_id": "CON_11",
                    "text": "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
                    "confidence_pct": 85,
                }
            )

        # Con Rule 12: Revenue CAGR < 5% over 5 years
        if rev_cagr_5 is not None and rev_cagr_5 < 5.0:
            cons.append(
                {
                    "rule_id": "CON_12",
                    "text": "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
                    "confidence_pct": 80,
                }
            )

        # Fallback Con if none matched
        if not cons:
            pe_val = latest_mcap.get("pe_ratio", 0) or 0
            if pe_val > 40.0:
                cons.append(
                    {
                        "rule_id": "CON_FALLBACK_VALUATION",
                        "text": "Elevated price-to-earnings valuation leaves limited margin of safety for future earnings misses",
                        "confidence_pct": 75,
                    }
                )
            elif rev_cagr_5 is not None and rev_cagr_5 < 10.0:
                cons.append(
                    {
                        "rule_id": "CON_FALLBACK_MODERATE_GROWTH",
                        "text": "Moderate top-line growth rate relative to high-performing industry peers",
                        "confidence_pct": 70,
                    }
                )
            elif latest_de > 0.8:
                cons.append(
                    {
                        "rule_id": "CON_FALLBACK_LEVERAGE",
                        "text": "Moderate debt obligations require ongoing cash allocation towards debt servicing",
                        "confidence_pct": 70,
                    }
                )
            else:
                cons.append(
                    {
                        "rule_id": "CON_FALLBACK_GENERIC",
                        "text": "Cyclical industry exposure and vulnerability to macroeconomic growth fluctuations",
                        "confidence_pct": 65,
                    }
                )

        # Append to results
        for p in pros:
            if p["confidence_pct"] > 60:
                results.append(
                    {
                        "company_id": comp_id,
                        "type": "pro",
                        "rule_id": p["rule_id"],
                        "text": p["text"],
                        "confidence_pct": p["confidence_pct"],
                    }
                )

        for c in cons:
            if c["confidence_pct"] > 60:
                results.append(
                    {
                        "company_id": comp_id,
                        "type": "con",
                        "rule_id": c["rule_id"],
                        "text": c["text"],
                        "confidence_pct": c["confidence_pct"],
                    }
                )

    df_out = pd.DataFrame(results)
    df_out.to_csv(output_path, index=False)
    print(
        f"Generated pros and cons for {len(companies)} companies -> {output_path} ({len(df_out)} total entries)"
    )

    # Verify coverage across all companies
    covered_comps = df_out["company_id"].unique()
    pro_comps = df_out[df_out["type"] == "pro"]["company_id"].unique()
    con_comps = df_out[df_out["type"] == "con"]["company_id"].unique()

    print(f"Verification: {len(covered_comps)}/92 companies covered.")
    print(f"Companies with at least 1 Pro: {len(pro_comps)}/92")
    print(f"Companies with at least 1 Con: {len(con_comps)}/92")

    return df_out


if __name__ == "__main__":
    generate_pros_and_cons()
