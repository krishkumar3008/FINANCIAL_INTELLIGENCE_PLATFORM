from fastapi import APIRouter, HTTPException

from src.database import get_db_connection

router = APIRouter()


@router.get(
    "/market-cap/{ticker}", summary="Get historical valuation multiples (2019-2024)"
)
def get_valuation_multiples(ticker: str):
    """
    Returns historical valuation multiples (P/E, P/B, EV/EBITDA, dividend yield) from 2019 to 2024.
    Returns HTTP 404 if ticker not found.
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

        query = """
        SELECT company_id, year, market_cap_crore, enterprise_value_crore,
               pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct
        FROM market_cap
        WHERE company_id = ? AND year BETWEEN 2019 AND 2024
        ORDER BY year ASC;
        """
        cur.execute(query, (t_upper,))
        rows = [dict(r) for r in cur.fetchall()]
        return {"company_id": t_upper, "valuation_history": rows}
    finally:
        conn.close()
