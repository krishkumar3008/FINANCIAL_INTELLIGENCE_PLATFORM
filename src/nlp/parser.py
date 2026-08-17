import os
import re
import sqlite3

import pandas as pd


def parse_analysis_file(
    filepath: str = "Dataset/analysis.xlsx",
    output_parsed: str = "output/analysis_parsed.csv",
    output_failures: str = "output/parse_failures.csv",
    db_path: str = "nifty100.db",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    r"""
    Parses text fields in analysis.xlsx using regex.
    Target fields: compounded_sales_growth, compounded_profit_growth, stock_price_cagr, roe
    Regex pattern: (\d+)\s*Years?:?\s*(-?[\d.]+)%
    """
    os.makedirs(os.path.dirname(output_parsed), exist_ok=True)

    if os.path.exists(filepath):
        # Header is on row index 1 (2nd row)
        df_raw = pd.read_excel(filepath, header=1)
    else:
        # Fallback to database analysis table if excel file not present
        conn = sqlite3.connect(db_path)
        df_raw = pd.read_sql("SELECT * FROM analysis", conn)
        conn.close()

    target_fields = [
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ]

    pattern = re.compile(r"(\d+)\s*Years?:?\s*(-?[\d.]+)%", re.IGNORECASE)

    parsed_records = []
    failure_records = []

    for _, row in df_raw.iterrows():
        company_id = str(row.get("company_id", "")).strip()
        if not company_id or company_id == "nan":
            continue

        for field in target_fields:
            if field not in row or pd.isna(row[field]):
                continue

            raw_val = str(row[field]).strip()
            # Split cell by newline or comma if multi-line
            lines = [l.strip() for l in raw_val.split("\n") if l.strip()]

            for line in lines:
                match = pattern.search(line)
                if match:
                    period_years = int(match.group(1))
                    value_pct = float(match.group(2))
                    parsed_records.append(
                        {
                            "company_id": company_id,
                            "metric_type": field,
                            "period_years": period_years,
                            "value_pct": value_pct,
                        }
                    )
                else:
                    failure_records.append(
                        {
                            "company_id": company_id,
                            "metric_type": field,
                            "raw_text": line,
                        }
                    )

    df_parsed = pd.DataFrame(parsed_records)
    df_failures = pd.DataFrame(failure_records)

    df_parsed.to_csv(output_parsed, index=False)
    df_failures.to_csv(output_failures, index=False)

    print(f"Parsing complete: {len(df_parsed)} records parsed -> {output_parsed}")
    print(f"Parsing failures logged: {len(df_failures)} records -> {output_failures}")

    # Cross-validate parsed CAGR with Ratio Engine if nifty100.db exists
    if os.path.exists(db_path):
        cross_validate_cagr(df_parsed, db_path=db_path)

    return df_parsed, df_failures


def cross_validate_cagr(
    df_parsed: pd.DataFrame, db_path: str = "nifty100.db"
) -> pd.DataFrame:
    """
    Cross-validates parsed 5-year CAGR values against computed CAGR from the Ratio Engine (financial_ratios).
    Flags divergence > 5% for manual review.
    """
    conn = sqlite3.connect(db_path)
    ratios_df = pd.read_sql(
        "SELECT company_id, revenue_cagr_5yr, pat_cagr_5yr FROM financial_ratios WHERE year = (SELECT MAX(year) FROM financial_ratios)",
        conn,
    )
    conn.close()

    divergent_records = []

    for _, row in df_parsed.iterrows():
        comp_id = row["company_id"]
        metric = row["metric_type"]
        period = row["period_years"]
        parsed_val = row["value_pct"]

        if period == 5 and metric in [
            "compounded_sales_growth",
            "compounded_profit_growth",
        ]:
            match = ratios_df[ratios_df["company_id"] == comp_id]
            if not match.empty:
                computed_val = None
                if metric == "compounded_sales_growth":
                    computed_val = match.iloc[0]["revenue_cagr_5yr"]
                elif metric == "compounded_profit_growth":
                    computed_val = match.iloc[0]["pat_cagr_5yr"]

                if computed_val is not None and not pd.isna(computed_val):
                    diff = abs(parsed_val - computed_val)
                    if diff > 5.0:
                        divergent_records.append(
                            {
                                "company_id": comp_id,
                                "metric_type": metric,
                                "parsed_value_pct": parsed_val,
                                "computed_cagr_5yr": computed_val,
                                "divergence_pct": diff,
                            }
                        )
                        print(
                            f"[FLAG] Divergence > 5% for {comp_id} ({metric}): Parsed={parsed_val}%, Computed={computed_val:.2f}% (Diff={diff:.2f}%)"
                        )

    df_div = pd.DataFrame(divergent_records)
    return df_div


if __name__ == "__main__":
    parse_analysis_file()
