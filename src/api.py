from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.database import get_db_connection

app = FastAPI(
    title="Nifty 100 Financial Intelligence Platform API",
    description="REST API for Sprint 1 Data Foundation",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def query_db(query: str, args: tuple = (), one: bool = False) -> Any:
    """Helper to query the SQLite database and return results as dictionary lists."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, args)
        rv = cursor.fetchall()
        # Convert sqlite3.Row to standard dict
        results = [dict(r) for r in rv]
        return (results[0] if results else None) if one else results
    finally:
        conn.close()


@app.get("/")
def read_root():
    """Returns database status and summary counts."""
    tables = [
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
        "prosandcons",
        "analysis",
    ]
    counts = {}
    for t in tables:
        try:
            res = query_db(f"SELECT COUNT(*) as cnt FROM {t};", one=True)
            counts[t] = res["cnt"] if res else 0
        except Exception:
            counts[t] = "error"

    return {
        "status": "online",
        "message": "Nifty 100 Financial Intelligence Platform API is running.",
        "database_counts": counts,
    }


@app.get("/companies")
def get_companies():
    """Retrieves all companies loaded in the database."""
    query = "SELECT * FROM companies ORDER BY company_name;"
    return query_db(query)


@app.get("/companies/{company_id}")
def get_company(company_id: str):
    """Retrieves a single company's details."""
    query = "SELECT * FROM companies WHERE id = ?;"
    res = query_db(query, (company_id.upper(),), one=True)
    if not res:
        raise HTTPException(
            status_code=404, detail=f"Company with ID '{company_id}' not found."
        )
    return res


@app.get("/companies/{company_id}/financials")
def get_company_financials(company_id: str):
    """Retrieves financial statements (P&L, Balance Sheet, Cash Flow, Ratios) for a company."""
    comp_id = company_id.upper()
    # Verify company exists
    company = query_db("SELECT id FROM companies WHERE id = ?;", (comp_id,), one=True)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{comp_id}' not found.")

    pl = query_db(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year;", (comp_id,)
    )
    bs = query_db(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year;", (comp_id,)
    )
    cf = query_db(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year;", (comp_id,)
    )
    ratios = query_db(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year;", (comp_id,)
    )
    market_cap = query_db(
        "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year;", (comp_id,)
    )
    sectors = query_db(
        "SELECT * FROM sectors WHERE company_id = ?;", (comp_id,), one=True
    )
    pros_cons = query_db(
        "SELECT * FROM prosandcons WHERE company_id = ?;", (comp_id,), one=True
    )
    analysis = query_db(
        "SELECT * FROM analysis WHERE company_id = ?;", (comp_id,), one=True
    )
    documents = query_db(
        "SELECT * FROM documents WHERE company_id = ? ORDER BY year;", (comp_id,)
    )

    return {
        "company_id": comp_id,
        "sector": sectors,
        "analysis": analysis,
        "pros_cons": pros_cons,
        "profit_and_loss": pl,
        "balance_sheet": bs,
        "cash_flow": cf,
        "ratios": ratios,
        "market_cap": market_cap,
        "documents": documents,
    }


@app.get("/companies/{company_id}/prices")
def get_company_prices(company_id: str):
    """Retrieves stock price history for a company."""
    comp_id = company_id.upper()
    company = query_db("SELECT id FROM companies WHERE id = ?;", (comp_id,), one=True)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{comp_id}' not found.")

    prices = query_db(
        "SELECT date, open_price, high_price, low_price, close_price, volume, adjusted_close FROM stock_prices WHERE company_id = ? ORDER BY date;",
        (comp_id,),
    )
    return {"company_id": comp_id, "prices": prices}
