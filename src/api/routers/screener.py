from fastapi import APIRouter, HTTPException, Query

from src.database import get_db_connection

router = APIRouter()


@router.get("/screener", summary="Screen companies with custom financial filters")
def run_screener(
    min_roe: float | None = Query(None, description="Minimum Return on Equity (%)"),
    max_de: float | None = Query(None, description="Maximum Debt to Equity ratio"),
    min_fcf: float | None = Query(None, description="Minimum Free Cash Flow (₹ Cr)"),
    sector: str | None = Query(None, description="Broad sector filter"),
    min_rev_cagr_5yr: float | None = Query(
        None, description="Minimum 5-Yr Revenue CAGR (%)"
    ),
    min_pat_cagr_5yr: float | None = Query(
        None, description="Minimum 5-Yr PAT CAGR (%)"
    ),
    max_pe: float | None = Query(None, description="Maximum P/E ratio"),
):
    """
    Screens and ranks companies based on financial criteria.
    Returns HTTP 400 for invalid parameter ranges or values.
    """
    # Parameter Validation (400 Bad Request)
    if max_de is not None and max_de < 0:
        raise HTTPException(status_code=400, detail="max_de cannot be negative.")
    if max_pe is not None and max_pe < 0:
        raise HTTPException(status_code=400, detail="max_pe cannot be negative.")
    if min_roe is not None and (min_roe < -100 or min_roe > 1000):
        raise HTTPException(
            status_code=400, detail="min_roe must be between -100 and 1000."
        )

    conn = get_db_connection()
    try:
        query = """
        SELECT c.id as company_id, c.company_name, s.broad_sector, s.sub_sector,
               COALESCE(fr.return_on_equity_pct, c.roe_percentage) as roe_pct,
               fr.debt_to_equity as de_ratio,
               fr.free_cash_flow_cr as fcf_cr,
               fr.revenue_cagr_5yr,
               fr.pat_cagr_5yr,
               mc.pe_ratio,
               mc.market_cap_crore
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        LEFT JOIN (
            SELECT company_id, return_on_equity_pct, debt_to_equity, free_cash_flow_cr,
                   revenue_cagr_5yr, pat_cagr_5yr
            FROM financial_ratios
            WHERE year != 9999
            GROUP BY company_id
            HAVING MAX(year)
        ) fr ON c.id = fr.company_id
        LEFT JOIN (
            SELECT company_id, pe_ratio, market_cap_crore
            FROM market_cap
            WHERE year != 9999
            GROUP BY company_id
            HAVING MAX(year)
        ) mc ON c.id = mc.company_id
        WHERE 1=1
        """
        params = []

        if sector:
            query += " AND LOWER(s.broad_sector) = LOWER(?)"
            params.append(sector)

        query += " ORDER BY roe_pct DESC;"

        cur = conn.cursor()
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]

        # Filter in Python for edge cases & None handling
        filtered = []
        for r in rows:
            roe = r.get("roe_pct")
            de = r.get("de_ratio")
            fcf = r.get("fcf_cr")
            rev_cagr = r.get("revenue_cagr_5yr")
            pat_cagr = r.get("pat_cagr_5yr")
            pe = r.get("pe_ratio")

            if min_roe is not None and (roe is None or roe < min_roe):
                continue
            if max_de is not None and (de is None or de > max_de):
                continue
            if min_fcf is not None and (fcf is None or fcf < min_fcf):
                continue
            if min_rev_cagr_5yr is not None and (
                rev_cagr is None or rev_cagr < min_rev_cagr_5yr
            ):
                continue
            if min_pat_cagr_5yr is not None and (
                pat_cagr is None or pat_cagr < min_pat_cagr_5yr
            ):
                continue
            if max_pe is not None and (pe is None or pe > max_pe):
                continue

            filtered.append(r)

        return filtered
    finally:
        conn.close()
