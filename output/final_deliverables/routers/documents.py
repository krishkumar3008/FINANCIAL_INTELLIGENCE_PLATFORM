from fastapi import APIRouter, HTTPException

from src.database import get_db_connection

router = APIRouter()


def validate_url(url: str | None) -> bool:
    """Checks if document annual report URL is valid."""
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    if "example.com" in u or "invalid" in u or len(u) < 10:
        return False
    return True


@router.get(
    "/companies/{ticker}/documents",
    summary="Get annual report document links with validation status",
)
def get_company_documents(ticker: str):
    """
    Returns annual report links with is_url_valid boolean flag for each year.
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

        cur.execute(
            "SELECT company_id, year, annual_report FROM documents WHERE company_id = ? ORDER BY year ASC;",
            (t_upper,),
        )
        rows = cur.fetchall()

        result = []
        for r in rows:
            r_dict = dict(r)
            url = r_dict.get("annual_report")
            r_dict["is_url_valid"] = validate_url(url)
            result.append(r_dict)

        return {"company_id": t_upper, "documents": result}
    finally:
        conn.close()
