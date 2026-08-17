import time

from fastapi import APIRouter

from src.database import get_db_connection

router = APIRouter()
START_TIME = time.time()

TABLES = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios",
    "market_cap",
    "sectors",
    "stock_prices",
    "peer_groups",
    "documents",
]


@router.get("/health", summary="Get system health and DB table row counts")
def get_health():
    """
    Returns system status, database table row counts, uptime, and version.
    """
    conn = get_db_connection()
    db_row_counts = {}
    try:
        cursor = conn.cursor()
        for t in TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {t};")
                row = cursor.fetchone()
                db_row_counts[t] = row[0] if row else 0
            except Exception:
                db_row_counts[t] = 0
    finally:
        conn.close()

    uptime = round(time.time() - START_TIME, 2)
    return {
        "status": "ok",
        "db_row_counts": db_row_counts,
        "uptime_seconds": uptime,
        "version": "1.0.0",
    }
