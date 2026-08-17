import sqlite3


def apply_db_indexes(db_path: str = "nifty100.db"):
    """
    Applies performance indexes on company_id and year columns across database tables.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_pnl_comp_yr ON profitandloss(company_id, year);",
        "CREATE INDEX IF NOT EXISTS idx_bs_comp_yr ON balancesheet(company_id, year);",
        "CREATE INDEX IF NOT EXISTS idx_cf_comp_yr ON cashflow(company_id, year);",
        "CREATE INDEX IF NOT EXISTS idx_ratios_comp_yr ON financial_ratios(company_id, year);",
        "CREATE INDEX IF NOT EXISTS idx_mcap_comp_yr ON market_cap(company_id, year);",
        "CREATE INDEX IF NOT EXISTS idx_docs_comp_yr ON documents(company_id, year);",
        "CREATE INDEX IF NOT EXISTS idx_sectors_comp ON sectors(company_id);",
        "CREATE INDEX IF NOT EXISTS idx_stock_comp_date ON stock_prices(company_id, date);",
    ]

    for idx_sql in indexes:
        cur.execute(idx_sql)

    conn.commit()
    conn.close()
    print("[OK] Applied performance indexes to database.")


if __name__ == "__main__":
    apply_db_indexes()
