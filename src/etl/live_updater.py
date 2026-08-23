import os
import sqlite3
import datetime
import logging
import pandas as pd
import yfinance as yf
from src.database import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ticker overrides for Yahoo Finance if symbol differs from DB ID
TICKER_OVERRIDES = {
    "M&M": "M&M.NS",
    "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
    "BAJAJFINSV": "BAJAJFINSV.NS",
    "BAJAJHLDNG": "BAJAJHLDNG.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "TATASTEEL": "TATASTEEL.NS",
    "TATACONSUM": "TATACONSUM.NS",
    "LTIM": "LTIM.NS",
    "M&MFIN": "M&MFIN.NS",
}


def get_yf_symbol(company_id: str) -> str:
    """Returns Yahoo Finance ticker string for a company ID."""
    if company_id in TICKER_OVERRIDES:
        return TICKER_OVERRIDES[company_id]
    return f"{company_id}.NS"


def get_existing_tickers(db_path: str = "nifty100.db") -> list[str]:
    """Retrieves list of company tickers from database."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id FROM companies ORDER BY id").fetchall()
        return [r["id"] for r in rows]
    finally:
        conn.close()


def fetch_and_update_prices(
    db_path: str = "nifty100.db",
    start_date: str = "2024-12-01",
    end_date: str = None
) -> int:
    """
    Fetches daily OHLCV prices from start_date to today using yfinance
    and upserts them into stock_prices table in SQLite.
    Returns the total number of inserted/updated records.
    """
    tickers = get_existing_tickers(db_path)
    if not tickers:
        logger.warning("No companies found in database.")
        return 0

    if end_date is None:
        end_date = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    yf_symbols = [get_yf_symbol(t) for t in tickers]
    symbol_to_company = {get_yf_symbol(t): t for t in tickers}

    logger.info(f"Downloading market data for {len(tickers)} companies from {start_date} to {end_date}...")
    
    try:
        data = yf.download(
            tickers=yf_symbols,
            start=start_date,
            end=end_date,
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True
        )
    except Exception as e:
        logger.error(f"Error executing yfinance batch download: {e}")
        return 0

    conn = get_db_connection(db_path)
    records_inserted = 0

    try:
        cursor = conn.cursor()
        for yf_sym in yf_symbols:
            company_id = symbol_to_company[yf_sym]
            try:
                if len(yf_symbols) == 1:
                    df = data
                else:
                    if yf_sym not in data.columns.levels[0]:
                        continue
                    df = data[yf_sym]

                df = df.dropna(how="all")
                if df.empty:
                    continue

                for dt_index, row in df.iterrows():
                    date_str = dt_index.strftime("%Y-%m-%d")
                    open_p = float(row["Open"]) if pd.notna(row["Open"]) else None
                    high_p = float(row["High"]) if pd.notna(row["High"]) else None
                    low_p = float(row["Low"]) if pd.notna(row["Low"]) else None
                    close_p = float(row["Close"]) if pd.notna(row["Close"]) else None
                    adj_close = float(row["Adj Close"]) if "Adj Close" in row and pd.notna(row["Adj Close"]) else close_p
                    vol = int(row["Volume"]) if pd.notna(row["Volume"]) else 0

                    if close_p is None:
                        continue

                    # Upsert into stock_prices table
                    cursor.execute(
                        """
                        INSERT INTO stock_prices (company_id, date, open_price, high_price, low_price, close_price, volume, adjusted_close)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(company_id, date) DO UPDATE SET
                            open_price=excluded.open_price,
                            high_price=excluded.high_price,
                            low_price=excluded.low_price,
                            close_price=excluded.close_price,
                            volume=excluded.volume,
                            adjusted_close=excluded.adjusted_close
                        """,
                        (company_id, date_str, open_p, high_p, low_p, close_p, vol, adj_close)
                    )
                    records_inserted += 1

            except Exception as e:
                logger.warning(f"Error processing ticker {company_id} ({yf_sym}): {e}")
                continue

        conn.commit()
        logger.info(f"Successfully updated stock_prices with {records_inserted} rows.")
    finally:
        conn.close()

    return records_inserted


if __name__ == "__main__":
    logger.info("Starting live market data update...")
    inserted = fetch_and_update_prices()
    logger.info(f"Finished live update. Total rows processed: {inserted}")
