import os

import pandas as pd
from fastapi import APIRouter

from src.database import get_db_connection

router = APIRouter()

PORTFOLIO_STATS_CSV = "output/portfolio_stats.csv"


@router.get("/portfolio/stats", summary="Get P10 through P90 portfolio KPI statistics")
def get_portfolio_stats():
    """
    Returns P10, P25, P50, P75, P90, Mean, and Std percentile table for 10 core KPIs across all 92 companies.
    """
    if os.path.exists(PORTFOLIO_STATS_CSV):
        df_stats = pd.read_csv(PORTFOLIO_STATS_CSV)
        return df_stats.to_dict(orient="records")

    conn = get_db_connection()
    try:
        kpi_cols = [
            "return_on_equity_pct",
            "operating_profit_margin_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
        ]
        query = """
        SELECT company_id, return_on_equity_pct, operating_profit_margin_pct, net_profit_margin_pct,
               debt_to_equity, interest_coverage, asset_turnover, revenue_cagr_5yr, pat_cagr_5yr
        FROM financial_ratios
        WHERE year != 9999
        GROUP BY company_id HAVING MAX(year);
        """
        df = pd.read_sql(query, conn)

        stats_data = []
        for col in kpi_cols:
            s = df[col].dropna()
            if not s.empty:
                stats_data.append(
                    {
                        "metric": col,
                        "P10": round(float(s.quantile(0.10)), 2),
                        "P25": round(float(s.quantile(0.25)), 2),
                        "P50": round(float(s.quantile(0.50)), 2),
                        "P75": round(float(s.quantile(0.75)), 2),
                        "P90": round(float(s.quantile(0.90)), 2),
                        "Mean": round(float(s.mean()), 2),
                        "Std": round(float(s.std()), 2),
                    }
                )
        return stats_data
    finally:
        conn.close()
