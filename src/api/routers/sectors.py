
import pandas as pd
from fastapi import APIRouter, HTTPException

from src.database import get_db_connection

router = APIRouter()


@router.get("/sectors", summary="Get 11 broad sectors summary")
def get_sectors():
    """
    Returns summary statistics for all 11 broad sectors:
    company_count, median_roe, median_pe, median_de.
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT c.id as company_id, s.broad_sector,
               COALESCE(fr.return_on_equity_pct, c.roe_percentage) as roe_pct,
               fr.debt_to_equity as de_ratio,
               mc.pe_ratio
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        LEFT JOIN (
            SELECT company_id, return_on_equity_pct, debt_to_equity
            FROM financial_ratios WHERE year != 9999
            GROUP BY company_id HAVING MAX(year)
        ) fr ON c.id = fr.company_id
        LEFT JOIN (
            SELECT company_id, pe_ratio
            FROM market_cap WHERE year != 9999
            GROUP BY company_id HAVING MAX(year)
        ) mc ON c.id = mc.company_id
        """
        df = pd.read_sql(query, conn)

        result = []
        for sector_name, grp in df.groupby("broad_sector"):
            c_cnt = len(grp)
            m_roe = (
                round(grp["roe_pct"].median(), 2)
                if not grp["roe_pct"].dropna().empty
                else None
            )
            m_pe = (
                round(grp["pe_ratio"].median(), 2)
                if not grp["pe_ratio"].dropna().empty
                else None
            )
            m_de = (
                round(grp["de_ratio"].median(), 2)
                if not grp["de_ratio"].dropna().empty
                else None
            )

            result.append(
                {
                    "broad_sector": sector_name,
                    "company_count": c_cnt,
                    "median_roe": m_roe,
                    "median_pe": m_pe,
                    "median_de": m_de,
                }
            )

        result = sorted(result, key=lambda x: x["broad_sector"])
        return result
    finally:
        conn.close()


@router.get(
    "/sectors/{sector}/companies", summary="Get companies in a sector with latest KPIs"
)
def get_sector_companies(sector: str):
    """
    Returns all companies in a broad sector with latest year KPIs.
    Returns HTTP 404 if sector is unknown.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT broad_sector FROM sectors WHERE LOWER(broad_sector) = LOWER(?);",
            (sector,),
        )
        sector_row = cur.fetchone()
        if not sector_row:
            raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found.")

        exact_sector = sector_row[0]

        query = """
        SELECT c.id as company_id, c.company_name, s.broad_sector, s.sub_sector,
               COALESCE(fr.return_on_equity_pct, c.roe_percentage) as roe_pct,
               COALESCE(fr.operating_profit_margin_pct, 0) as opm_pct,
               fr.debt_to_equity as de_ratio,
               fr.revenue_cagr_5yr,
               mc.pe_ratio,
               mc.market_cap_crore
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        LEFT JOIN (
            SELECT company_id, return_on_equity_pct, operating_profit_margin_pct, debt_to_equity, revenue_cagr_5yr
            FROM financial_ratios WHERE year != 9999
            GROUP BY company_id HAVING MAX(year)
        ) fr ON c.id = fr.company_id
        LEFT JOIN (
            SELECT company_id, pe_ratio, market_cap_crore
            FROM market_cap WHERE year != 9999
            GROUP BY company_id HAVING MAX(year)
        ) mc ON c.id = mc.company_id
        WHERE LOWER(s.broad_sector) = LOWER(?)
        ORDER BY c.id ASC;
        """
        cur.execute(query, (sector,))
        rows = [dict(r) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()
