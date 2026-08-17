import re

import pandas as pd


def validate_data(
    companies_df: pd.DataFrame,
    pl_df: pd.DataFrame,
    bs_df: pd.DataFrame,
    cf_df: pd.DataFrame,
    analysis_df: pd.DataFrame,
    docs_df: pd.DataFrame,
    pros_df: pd.DataFrame,
    sectors_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    ratios_df: pd.DataFrame,
    peers_df: pd.DataFrame,
    market_cap_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Runs all 16 Data Quality (DQ) rules on the raw/normalized datasets.
    Returns a DataFrame of validation failures with columns:
      - rule_id: str (DQ-01 to DQ-16)
      - table_name: str
      - record_id: str
      - field_name: str
      - actual_value: str
      - expected_value: str
      - severity: str ('CRITICAL' or 'WARNING')
      - description: str
    """
    failures = []

    def log_failure(rule_id, table, rec_id, field, actual, expected, severity, desc):
        failures.append(
            {
                "rule_id": rule_id,
                "table_name": table,
                "record_id": str(rec_id),
                "field_name": field,
                "actual_value": str(actual),
                "expected_value": str(expected),
                "severity": severity,
                "description": desc,
            }
        )

    # Get set of valid company IDs from companies table
    comp_ids = (
        set(companies_df["id"].dropna().astype(str).tolist())
        if "id" in companies_df.columns
        else set()
    )

    # Helpers for URL regex
    url_pattern = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

    # ----------------------------------------------------
    # DQ-01: Primary Key Uniqueness (CRITICAL)
    # ----------------------------------------------------
    tables_to_check_pk = [
        (companies_df, "companies", "id"),
        (pl_df, "profitandloss", "id"),
        (bs_df, "balancesheet", "id"),
        (cf_df, "cashflow", "id"),
        (analysis_df, "analysis", "id"),
        (docs_df, "documents", "id"),
        (pros_df, "prosandcons", "id"),
        (sectors_df, "sectors", "id"),
        (prices_df, "stock_prices", "id"),
        (ratios_df, "financial_ratios", "id"),
        (peers_df, "peer_groups", "id"),
        (market_cap_df, "market_cap", "id"),
    ]
    for df, name, pk in tables_to_check_pk:
        if df is not None and pk in df.columns:
            dups = df[df.duplicated(subset=[pk], keep=False)]
            for _, row in dups.iterrows():
                log_failure(
                    "DQ-01",
                    name,
                    row[pk],
                    pk,
                    row[pk],
                    "unique",
                    "CRITICAL",
                    f"Duplicate primary key '{row[pk]}' in table '{name}'",
                )

    # ----------------------------------------------------
    # DQ-02: Composite Primary Key (company_id, year) Uniqueness (CRITICAL)
    # ----------------------------------------------------
    tables_to_check_composite = [
        (pl_df, "profitandloss", "year"),
        (bs_df, "balancesheet", "year"),
        (cf_df, "cashflow", "year"),
        (ratios_df, "financial_ratios", "year"),
        (market_cap_df, "market_cap", "year"),
    ]
    for df, name, year_col in tables_to_check_composite:
        if df is not None and "company_id" in df.columns and year_col in df.columns:
            dups = df[df.duplicated(subset=["company_id", year_col], keep=False)]
            for _, row in dups.iterrows():
                rec_id = f"{row['company_id']}_{row[year_col]}"
                log_failure(
                    "DQ-02",
                    name,
                    rec_id,
                    f"company_id, {year_col}",
                    rec_id,
                    "unique (company_id, year)",
                    "CRITICAL",
                    f"Duplicate composite key (company_id, year) for '{rec_id}' in table '{name}'",
                )

    # ----------------------------------------------------
    # DQ-03: Foreign Key Integrity (CRITICAL)
    # ----------------------------------------------------
    child_tables = [
        (pl_df, "profitandloss"),
        (bs_df, "balancesheet"),
        (cf_df, "cashflow"),
        (analysis_df, "analysis"),
        (docs_df, "documents"),
        (pros_df, "prosandcons"),
        (sectors_df, "sectors"),
        (prices_df, "stock_prices"),
        (ratios_df, "financial_ratios"),
        (peers_df, "peer_groups"),
        (market_cap_df, "market_cap"),
    ]
    for df, name in child_tables:
        if df is not None and "company_id" in df.columns:
            missing_fks = df[~df["company_id"].isin(comp_ids)]
            for _, row in missing_fks.iterrows():
                rec_id = row["id"] if "id" in df.columns else row["company_id"]
                log_failure(
                    "DQ-03",
                    name,
                    rec_id,
                    "company_id",
                    row["company_id"],
                    "exists in companies",
                    "CRITICAL",
                    f"Foreign key violation: company_id '{row['company_id']}' does not exist in 'companies' table",
                )

    # ----------------------------------------------------
    # DQ-04: Balance Sheet Balance (WARNING)
    # ----------------------------------------------------
    if bs_df is not None:
        required_cols = ["company_id", "year", "total_assets", "total_liabilities"]
        if all(c in bs_df.columns for c in required_cols):
            for _, row in bs_df.iterrows():
                ta = (
                    float(row["total_assets"]) if pd.notna(row["total_assets"]) else 0.0
                )
                tl = (
                    float(row["total_liabilities"])
                    if pd.notna(row["total_liabilities"])
                    else 0.0
                )
                diff = abs(ta - tl)
                tolerance = 0.01 * max(abs(ta), 1.0)
                if diff > tolerance:
                    rec_id = f"{row['company_id']}_{row['year']}"
                    log_failure(
                        "DQ-04",
                        "balancesheet",
                        rec_id,
                        "total_assets vs total_liabilities",
                        f"assets={ta}, liab={tl}",
                        "difference < 1%",
                        "WARNING",
                        f"Balance sheet does not balance: assets={ta}, liabilities={tl} (diff={diff:.2f})",
                    )

    # ----------------------------------------------------
    # DQ-05: OPM Cross-check (WARNING)
    # ----------------------------------------------------
    if pl_df is not None:
        required_cols = [
            "company_id",
            "year",
            "sales",
            "operating_profit",
            "opm_percentage",
        ]
        if all(c in pl_df.columns for c in required_cols):
            for _, row in pl_df.iterrows():
                sales = float(row["sales"]) if pd.notna(row["sales"]) else 0.0
                op = (
                    float(row["operating_profit"])
                    if pd.notna(row["operating_profit"])
                    else 0.0
                )
                opm = (
                    float(row["opm_percentage"])
                    if pd.notna(row["opm_percentage"])
                    else 0.0
                )

                # Check only if sales is positive
                if sales > 0:
                    calc_opm = (op / sales) * 100
                    # Check absolute difference
                    if abs(opm - calc_opm) > 1.0:
                        rec_id = f"{row['company_id']}_{row['year']}"
                        log_failure(
                            "DQ-05",
                            "profitandloss",
                            rec_id,
                            "opm_percentage",
                            f"opm_percentage={opm:.2f}%, calc={calc_opm:.2f}%",
                            "opm_percentage matches calc within 1%",
                            "WARNING",
                            f"OPM margin cross-check failed: reported={opm:.2f}%, calculated={calc_opm:.2f}%",
                        )

    # ----------------------------------------------------
    # DQ-06: Positive Sales (WARNING)
    # ----------------------------------------------------
    if pl_df is not None and "sales" in pl_df.columns:
        for _, row in pl_df.iterrows():
            sales = float(row["sales"]) if pd.notna(row["sales"]) else 0.0
            # Skip TTM year for this rule if it represents temporary data,
            # but we can apply it generally. Let's apply to all.
            if sales <= 0:
                rec_id = f"{row['company_id']}_{row['year']}"
                log_failure(
                    "DQ-06",
                    "profitandloss",
                    rec_id,
                    "sales",
                    sales,
                    "> 0",
                    "WARNING",
                    f"Non-positive sales/revenue: {sales}",
                )

    # ----------------------------------------------------
    # DQ-07: Net Cash Flow Consistency (WARNING)
    # ----------------------------------------------------
    if cf_df is not None:
        required_cols = [
            "company_id",
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ]
        if all(c in cf_df.columns for c in required_cols):
            for _, row in cf_df.iterrows():
                ops = (
                    float(row["operating_activity"])
                    if pd.notna(row["operating_activity"])
                    else 0.0
                )
                inv = (
                    float(row["investing_activity"])
                    if pd.notna(row["investing_activity"])
                    else 0.0
                )
                fin = (
                    float(row["financing_activity"])
                    if pd.notna(row["financing_activity"])
                    else 0.0
                )
                ncf = (
                    float(row["net_cash_flow"])
                    if pd.notna(row["net_cash_flow"])
                    else 0.0
                )

                calc_ncf = ops + inv + fin
                diff = abs(ncf - calc_ncf)
                tolerance = 0.01 * max(abs(ncf), 1.0)
                if diff > tolerance:
                    rec_id = f"{row['company_id']}_{row['year']}"
                    log_failure(
                        "DQ-07",
                        "cashflow",
                        rec_id,
                        "net_cash_flow",
                        f"ncf={ncf}, calc={calc_ncf}",
                        "difference < 1%",
                        "WARNING",
                        f"Net cash flow mismatch: reported={ncf}, sum of activities={calc_ncf} (diff={diff:.2f})",
                    )

    # ----------------------------------------------------
    # DQ-08: Tax Rate Check (WARNING)
    # ----------------------------------------------------
    if pl_df is not None:
        required_cols = ["company_id", "year", "profit_before_tax", "tax_percentage"]
        if all(c in pl_df.columns for c in required_cols):
            for _, row in pl_df.iterrows():
                pbt = (
                    float(row["profit_before_tax"])
                    if pd.notna(row["profit_before_tax"])
                    else 0.0
                )
                tax_pct = (
                    float(row["tax_percentage"])
                    if pd.notna(row["tax_percentage"])
                    else 0.0
                )

                if pbt > 0 and (tax_pct < 0 or tax_pct > 100):
                    rec_id = f"{row['company_id']}_{row['year']}"
                    log_failure(
                        "DQ-08",
                        "profitandloss",
                        rec_id,
                        "tax_percentage",
                        tax_pct,
                        "between 0 and 100",
                        "WARNING",
                        f"Unusual tax rate of {tax_pct}% with positive profit before tax of {pbt}",
                    )

    # ----------------------------------------------------
    # DQ-09: Dividend Cap Check (WARNING)
    # ----------------------------------------------------
    if pl_df is not None:
        required_cols = ["company_id", "year", "net_profit", "dividend_payout"]
        if all(c in pl_df.columns for c in required_cols):
            for _, row in pl_df.iterrows():
                np_val = (
                    float(row["net_profit"]) if pd.notna(row["net_profit"]) else 0.0
                )
                div_payout = (
                    float(row["dividend_payout"])
                    if pd.notna(row["dividend_payout"])
                    else 0.0
                )

                if np_val > 0 and div_payout > 100:
                    rec_id = f"{row['company_id']}_{row['year']}"
                    log_failure(
                        "DQ-09",
                        "profitandloss",
                        rec_id,
                        "dividend_payout",
                        div_payout,
                        "<= 100%",
                        "WARNING",
                        f"Dividend payout ratio {div_payout}% exceeds net profit of {np_val}",
                    )

    # ----------------------------------------------------
    # DQ-10: URL Format Validation (WARNING)
    # ----------------------------------------------------
    # Check websites in companies
    if companies_df is not None:
        url_fields = ["website", "nse_profile", "bse_profile"]
        for field in url_fields:
            if field in companies_df.columns:
                for _, row in companies_df.iterrows():
                    val = row[field]
                    if pd.notna(val) and str(val).strip():
                        if not url_pattern.match(str(val).strip()):
                            log_failure(
                                "DQ-10",
                                "companies",
                                row["id"],
                                field,
                                val,
                                "valid http/https URL",
                                "WARNING",
                                f"Invalid URL format for '{field}': '{val}'",
                            )
    # Check Annual Report links in documents
    if docs_df is not None:
        field = "Annual_Report"
        if field in docs_df.columns:
            for _, row in docs_df.iterrows():
                val = row[field]
                if pd.notna(val) and str(val).strip():
                    if not url_pattern.match(str(val).strip()):
                        rec_id = (
                            row["id"] if "id" in docs_df.columns else row["company_id"]
                        )
                        log_failure(
                            "DQ-10",
                            "documents",
                            rec_id,
                            field,
                            val,
                            "valid http/https URL",
                            "WARNING",
                            f"Invalid URL format for '{field}': '{val}'",
                        )

    # ----------------------------------------------------
    # DQ-11: EPS Sign Consistency (WARNING)
    # ----------------------------------------------------
    if pl_df is not None:
        required_cols = ["company_id", "year", "net_profit", "eps"]
        if all(c in pl_df.columns for c in required_cols):
            for _, row in pl_df.iterrows():
                np_val = (
                    float(row["net_profit"]) if pd.notna(row["net_profit"]) else 0.0
                )
                eps_val = float(row["eps"]) if pd.notna(row["eps"]) else 0.0

                # Verify signs match
                if (np_val > 0 and eps_val < 0) or (np_val < 0 and eps_val > 0):
                    rec_id = f"{row['company_id']}_{row['year']}"
                    log_failure(
                        "DQ-11",
                        "profitandloss",
                        rec_id,
                        "eps vs net_profit",
                        f"net_profit={np_val}, eps={eps_val}",
                        "matching signs",
                        "WARNING",
                        f"EPS sign mismatch: net profit is {np_val} but EPS is {eps_val}",
                    )

    # ----------------------------------------------------
    # DQ-12: Ticker Validity (WARNING)
    # ----------------------------------------------------
    if companies_df is not None:
        for _, row in companies_df.iterrows():
            comp_id = str(row["id"]).strip()
            # Symbol alphanumeric check
            if not re.match(r"^[A-Z0-9&-]+$", comp_id):
                log_failure(
                    "DQ-12",
                    "companies",
                    comp_id,
                    "id",
                    comp_id,
                    "alphanumeric, uppercase, symbols allowed: & or -",
                    "WARNING",
                    f"Ticker '{comp_id}' contains invalid characters",
                )

            # BSE ticker validation (extract from URL and check if 6 digit numeric)
            bse_prof = row.get("bse_profile")
            if pd.notna(bse_prof) and str(bse_prof).strip():
                # Extract trailing code, e.g. /500002/ or symbol code
                digits_match = re.search(r"/(\d{6})/?", str(bse_prof))
                if not digits_match:
                    log_failure(
                        "DQ-12",
                        "companies",
                        comp_id,
                        "bse_profile",
                        bse_prof,
                        "BSE profile URL containing 6-digit numeric ticker",
                        "WARNING",
                        f"BSE profile URL does not contain a valid 6-digit ticker code for '{comp_id}'",
                    )

    # ----------------------------------------------------
    # DQ-13: Interest Coverage Ratio Cross-Check (WARNING)
    # ----------------------------------------------------
    # Check if interest_coverage in financial_ratios is positive or matches operating_profit / interest
    if ratios_df is not None and pl_df is not None:
        required_ratio = ["company_id", "year", "interest_coverage"]
        required_pl = ["company_id", "year", "operating_profit", "interest"]
        if all(c in ratios_df.columns for c in required_ratio) and all(
            c in pl_df.columns for c in required_pl
        ):
            # Create a dictionary for quick P&L lookup
            pl_dict = {}
            for _, row in pl_df.iterrows():
                key = (row["company_id"], row["year"])
                pl_dict[key] = {
                    "op": (
                        float(row["operating_profit"])
                        if pd.notna(row["operating_profit"])
                        else 0.0
                    ),
                    "int": float(row["interest"]) if pd.notna(row["interest"]) else 0.0,
                }

            for _, row in ratios_df.iterrows():
                r_cov = (
                    float(row["interest_coverage"])
                    if pd.notna(row["interest_coverage"])
                    else None
                )
                if r_cov is not None:
                    key = (row["company_id"], row["year"])
                    if key in pl_dict:
                        pl_data = pl_dict[key]
                        op = pl_data["op"]
                        interest_val = pl_data["int"]
                        if interest_val > 0:
                            calc_cov = op / interest_val
                            # Tolerance check
                            if (
                                calc_cov > 0
                                and abs(r_cov - calc_cov) / calc_cov > 0.1
                                and abs(r_cov - calc_cov) > 1.0
                            ):
                                rec_id = f"{row['company_id']}_{row['year']}"
                                log_failure(
                                    "DQ-13",
                                    "financial_ratios",
                                    rec_id,
                                    "interest_coverage",
                                    f"reported={r_cov}, calc={calc_cov:.2f}",
                                    "interest coverage matches operating_profit / interest",
                                    "WARNING",
                                    f"Interest coverage ratio mismatch: reported={r_cov}, calculated={calc_cov:.2f}",
                                )

    # ----------------------------------------------------
    # DQ-14: Positive Assets/Equity Check (WARNING)
    # ----------------------------------------------------
    if bs_df is not None:
        required_cols = [
            "company_id",
            "year",
            "total_assets",
            "equity_capital",
            "reserves",
        ]
        if all(c in bs_df.columns for c in required_cols):
            for _, row in bs_df.iterrows():
                ta = (
                    float(row["total_assets"]) if pd.notna(row["total_assets"]) else 0.0
                )
                eq = (
                    float(row["equity_capital"])
                    if pd.notna(row["equity_capital"])
                    else 0.0
                )
                res = float(row["reserves"]) if pd.notna(row["reserves"]) else 0.0
                equity = eq + res

                rec_id = f"{row['company_id']}_{row['year']}"
                if ta <= 0:
                    log_failure(
                        "DQ-14",
                        "balancesheet",
                        rec_id,
                        "total_assets",
                        ta,
                        "> 0",
                        "WARNING",
                        f"Non-positive total assets: {ta}",
                    )
                if equity <= 0:
                    log_failure(
                        "DQ-14",
                        "balancesheet",
                        rec_id,
                        "equity_capital + reserves",
                        equity,
                        "> 0",
                        "WARNING",
                        f"Non-positive shareholder equity: {equity} (capital={eq}, reserves={res})",
                    )

    # ----------------------------------------------------
    # DQ-15: Year Coverage Check (WARNING)
    # ----------------------------------------------------
    # Each company should have at least 5 years of data in profitandloss
    if pl_df is not None and "company_id" in pl_df.columns:
        # Filter out TTM for count
        pl_no_ttm = pl_df[pl_df["year"].astype(str) != "TTM"]
        counts = pl_no_ttm.groupby("company_id").size()
        for comp, count in counts.items():
            if count < 5:
                log_failure(
                    "DQ-15",
                    "profitandloss",
                    comp,
                    "year_coverage",
                    count,
                    ">= 5 years",
                    "WARNING",
                    f"Company '{comp}' has only {count} years of financial records in P&L (minimum 5 expected)",
                )

    # ----------------------------------------------------
    # DQ-16: Price Uniqueness Check (CRITICAL)
    # ----------------------------------------------------
    if prices_df is not None:
        required_cols = ["company_id", "date"]
        if all(c in prices_df.columns for c in required_cols):
            dups = prices_df[
                prices_df.duplicated(subset=["company_id", "date"], keep=False)
            ]
            for _, row in dups.iterrows():
                rec_id = f"{row['company_id']}_{row['date']}"
                log_failure(
                    "DQ-16",
                    "stock_prices",
                    rec_id,
                    "company_id, date",
                    rec_id,
                    "unique (company_id, date)",
                    "CRITICAL",
                    f"Duplicate price record for (company_id, date): '{rec_id}' in stock_prices",
                )

    # Convert list of dicts to DataFrame
    return (
        pd.DataFrame(failures)
        if failures
        else pd.DataFrame(
            columns=[
                "rule_id",
                "table_name",
                "record_id",
                "field_name",
                "actual_value",
                "expected_value",
                "severity",
                "description",
            ]
        )
    )
