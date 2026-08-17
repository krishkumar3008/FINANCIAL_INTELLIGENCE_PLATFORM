import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.database import get_db_connection

router = APIRouter()


def helper_normalize_year_param(val: str | None) -> int | None:
    """Helper to parse year parameter string like '2020' or '2020-03' into integer year."""
    if not val:
        return None
    val_str = str(val).strip()
    if "-" in val_str:
        val_str = val_str.split("-")[0]
    try:
        return int(val_str)
    except ValueError:
        return None


@router.get("/companies", summary="List companies with optional filters")
def get_companies(
    sector: str | None = None,
    market_cap_category: str | None = None,
    search: str | None = None,
):
    """
    Returns list of companies with id, company_name, broad_sector, sub_sector, roe_pct, roce_pct.
    Supports optional filters: sector, market_cap_category, search.
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT c.id, c.company_name, s.broad_sector, s.sub_sector,
               c.roe_percentage as roe_pct, c.roce_percentage as roce_pct,
               s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        WHERE 1=1
        """
        params = []
        if sector:
            query += " AND LOWER(s.broad_sector) = LOWER(?)"
            params.append(sector)
        if market_cap_category:
            query += " AND LOWER(s.market_cap_category) = LOWER(?)"
            params.append(market_cap_category)
        if search:
            query += " AND (LOWER(c.id) LIKE LOWER(?) OR LOWER(c.company_name) LIKE LOWER(?))"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        query += " ORDER BY c.id ASC;"

        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            r_dict = dict(r)
            r_dict.pop("market_cap_category", None)
            result.append(r_dict)
        return result
    finally:
        conn.close()


@router.get("/companies/{ticker}", summary="Get full company profile")
def get_company_profile(ticker: str):
    """
    Returns full company profile including company details, latest year KPIs, and sector info.
    """
    t_upper = ticker.upper()
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM companies WHERE id = ?;", (t_upper,))
        comp = cur.fetchone()
        if not comp:
            raise HTTPException(
                status_code=404, detail=f"Company '{ticker}' not found."
            )

        comp_dict = dict(comp)

        # Sector data
        cur.execute("SELECT * FROM sectors WHERE company_id = ?;", (t_upper,))
        sec = cur.fetchone()
        comp_dict["sector_data"] = dict(sec) if sec else None

        # Latest financial ratios
        cur.execute(
            "SELECT * FROM financial_ratios WHERE company_id = ? AND year != 9999 ORDER BY year DESC LIMIT 1;",
            (t_upper,),
        )
        latest_r = cur.fetchone()
        comp_dict["latest_kpis"] = dict(latest_r) if latest_r else None

        return comp_dict
    finally:
        conn.close()


@router.get("/companies/{ticker}/pl", summary="Get P&L statement history")
def get_company_pnl(
    ticker: str, from_year: str | None = None, to_year: str | None = None
):
    """
    Returns Profit & Loss statement history array for company.
    """
    t_upper = ticker.upper()
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM companies WHERE id = ?;", (t_upper,))
        if not cur.fetchone():
            raise HTTPException(
                status_code=404, detail=f"Company '{ticker}' not found."
            )

        f_yr = helper_normalize_year_param(from_year)
        t_yr = helper_normalize_year_param(to_year)

        query = "SELECT * FROM profitandloss WHERE company_id = ? AND year != 9999"
        params = [t_upper]
        if f_yr is not None:
            query += " AND year >= ?"
            params.append(f_yr)
        if t_yr is not None:
            query += " AND year <= ?"
            params.append(t_yr)

        query += " ORDER BY year ASC;"
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/companies/{ticker}/bs", summary="Get Balance Sheet history")
def get_company_bs(
    ticker: str, from_year: str | None = None, to_year: str | None = None
):
    """
    Returns Balance Sheet history array for company.
    """
    t_upper = ticker.upper()
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM companies WHERE id = ?;", (t_upper,))
        if not cur.fetchone():
            raise HTTPException(
                status_code=404, detail=f"Company '{ticker}' not found."
            )

        f_yr = helper_normalize_year_param(from_year)
        t_yr = helper_normalize_year_param(to_year)

        query = "SELECT * FROM balancesheet WHERE company_id = ? AND year != 9999"
        params = [t_upper]
        if f_yr is not None:
            query += " AND year >= ?"
            params.append(f_yr)
        if t_yr is not None:
            query += " AND year <= ?"
            params.append(t_yr)

        query += " ORDER BY year ASC;"
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/companies/{ticker}/cashflow", summary="Get Cash Flow statement history")
def get_company_cashflow(
    ticker: str, from_year: str | None = None, to_year: str | None = None
):
    """
    Returns Cash Flow statement history array for company.
    """
    t_upper = ticker.upper()
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM companies WHERE id = ?;", (t_upper,))
        if not cur.fetchone():
            raise HTTPException(
                status_code=404, detail=f"Company '{ticker}' not found."
            )

        f_yr = helper_normalize_year_param(from_year)
        t_yr = helper_normalize_year_param(to_year)

        query = "SELECT * FROM cashflow WHERE company_id = ? AND year != 9999"
        params = [t_upper]
        if f_yr is not None:
            query += " AND year >= ?"
            params.append(f_yr)
        if t_yr is not None:
            query += " AND year <= ?"
            params.append(t_yr)

        query += " ORDER BY year ASC;"
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@router.get("/companies/{ticker}/ratios", summary="Get financial ratios history")
def get_company_ratios(ticker: str, year: int | None = None):
    """
    Returns financial ratios array or single year ratio object.
    """
    t_upper = ticker.upper()
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM companies WHERE id = ?;", (t_upper,))
        if not cur.fetchone():
            raise HTTPException(
                status_code=404, detail=f"Company '{ticker}' not found."
            )

        query = "SELECT * FROM financial_ratios WHERE company_id = ?"
        params = [t_upper]
        if year is not None:
            query += " AND year = ?"
            params.append(year)
        else:
            query += " AND year != 9999"

        query += " ORDER BY year ASC;"
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        if year is not None:
            if not rows:
                raise HTTPException(
                    status_code=404,
                    detail=f"No ratios found for '{ticker}' in year {year}.",
                )
            return rows[0]
        return rows
    finally:
        conn.close()


@router.get("/companies/{ticker}/tearsheet", summary="Download company tearsheet PDF")
def get_company_tearsheet_pdf(ticker: str):
    """
    Returns pre-generated tearsheet PDF binary download for company.
    """
    t_upper = ticker.upper()
    pdf_path = f"reports/tearsheets/{t_upper}_tearsheet.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=404, detail=f"Tearsheet PDF for company '{ticker}' not found."
        )

    return FileResponse(
        path=pdf_path, filename=f"{t_upper}_tearsheet.pdf", media_type="application/pdf"
    )
