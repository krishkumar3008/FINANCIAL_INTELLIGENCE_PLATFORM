import sqlite3
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from src.database import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def compute_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes technical indicators and lag features on daily stock price DataFrame.
    DataFrame must contain columns: ['date', 'close_price', 'open_price', 'high_price', 'low_price', 'volume']
    """
    if len(df) < 30:
        return df

    df = df.sort_values("date").reset_index(drop=True)
    close = df["close_price"]

    # Moving Averages
    df["sma_20"] = close.rolling(window=20).mean()
    df["sma_50"] = close.rolling(window=50).mean()
    df["sma_20_ratio"] = (close / df["sma_20"]) - 1.0
    df["sma_50_ratio"] = (close / df["sma_50"]) - 1.0

    # RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss.replace(0, 1e-6))
    df["rsi_14"] = 100 - (100 / (1 + rs))

    # MACD (12, 26, 9)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema_12 - ema_26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_diff"] = df["macd"] - df["macd_signal"]

    # Bollinger Bands (20, 2)
    rolling_std = close.rolling(window=20).std()
    df["bb_upper"] = df["sma_20"] + (rolling_std * 2)
    df["bb_lower"] = df["sma_20"] - (rolling_std * 2)
    bb_range = df["bb_upper"] - df["bb_lower"]
    df["bb_bandwidth"] = bb_range / df["sma_20"]
    df["bb_percent"] = (close - df["bb_lower"]) / (bb_range.replace(0, 1e-6))

    # Volume Ratio & Volatility
    vol_sma20 = df["volume"].rolling(window=20).mean()
    df["vol_ratio"] = df["volume"] / vol_sma20.replace(0, 1)
    df["return_1d"] = close.pct_change(1)
    df["return_3d"] = close.pct_change(3)
    df["return_5d"] = close.pct_change(5)
    df["volatility_5d"] = df["return_1d"].rolling(window=5).std()

    # Target variables for ML
    df["target_next_close"] = close.shift(-1)
    df["target_next_open"] = df["open_price"].shift(-1)
    df["target_up"] = (df["target_next_close"] > close).astype(int)

    return df


FEATURE_COLS = [
    "sma_20_ratio", "sma_50_ratio", "rsi_14", "macd", "macd_signal", "macd_diff",
    "bb_bandwidth", "bb_percent", "vol_ratio", "return_1d", "return_3d", "return_5d", "volatility_5d"
]


def predict_stock_tomorrow(company_id: str, db_path: str = "nifty100.db") -> dict:
    """
    Trains ML models on historical prices for company_id and returns next-day market forecast
    including Opening Price Forecast, Closing Price Target, and Directional Signals.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        # Fetch company name
        comp_row = cursor.execute("SELECT company_name FROM companies WHERE id=?", (company_id,)).fetchone()
        company_name = comp_row["company_name"] if comp_row else company_id

        # Fetch stock price history
        query = """
            SELECT date, open_price, high_price, low_price, close_price, volume
            FROM stock_prices
            WHERE company_id=?
            ORDER BY date ASC
        """
        rows = cursor.execute(query, (company_id,)).fetchall()
        if not rows or len(rows) < 30:
            return {
                "company_id": company_id,
                "company_name": company_name,
                "error": "Insufficient price data to train model (requires >= 30 days)"
            }

        df = pd.DataFrame([dict(r) for r in rows])
        df = compute_technical_indicators(df)

        # Separate feature dataset for training (excluding last row which has unknown target)
        clean_df = df.dropna(subset=FEATURE_COLS + ["target_up", "target_next_close", "target_next_open"]).copy()
        if len(clean_df) < 20:
            return {
                "company_id": company_id,
                "company_name": company_name,
                "error": "Not enough valid indicator rows for model training"
            }

        X = clean_df[FEATURE_COLS]
        y_cls = clean_df["target_up"]
        y_reg_close = clean_df["target_next_close"]
        y_reg_open = clean_df["target_next_open"]

        # Train Classifier for Direction
        clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        clf.fit(X, y_cls)

        # Train Regressors for Next-Day Close & Next-Day Open Prices
        reg_close = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        reg_close.fit(X, y_reg_close)

        reg_open = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        reg_open.fit(X, y_reg_open)

        # Feature matrix for the latest available date
        latest_row = df.iloc[-1]
        latest_features = latest_row[FEATURE_COLS].to_frame().T.apply(pd.to_numeric, errors='coerce').fillna(0.0)

        # Probabilities
        prob_up = float(clf.predict_proba(latest_features)[0][1])
        prob_down = 1.0 - prob_up

        predicted_target_close = float(reg_close.predict(latest_features)[0])
        predicted_open_price = float(reg_open.predict(latest_features)[0])

        current_close = float(latest_row["close_price"])
        as_of_date = str(latest_row["date"])

        direction = "BULLISH" if prob_up >= 0.50 else "BEARISH"
        confidence_pct = round((prob_up if direction == "BULLISH" else prob_down) * 100, 1)

        # Price targets & Opening gap calculations
        price_change_pct = round(((predicted_target_close / current_close) - 1.0) * 100, 2)
        gap_pct = round(((predicted_open_price / current_close) - 1.0) * 100, 2)
        
        if gap_pct >= 0.15:
            gap_type = "GAP UP 🟢"
        elif gap_pct <= -0.15:
            gap_type = "GAP DOWN 🔴"
        else:
            gap_type = "FLAT OPEN ⚖️"

        atr_estimate = (float(latest_row["high_price"]) - float(latest_row["low_price"])) if pd.notna(latest_row["high_price"]) else current_close * 0.015
        stop_loss = round(current_close - (1.5 * atr_estimate) if direction == "BULLISH" else current_close + (1.5 * atr_estimate), 2)
        support = round(float(df["low_price"].tail(20).min()), 2)
        resistance = round(float(df["high_price"].tail(20).max()), 2)

        # Technical signals breakdown
        rsi_val = float(latest_row["rsi_14"]) if pd.notna(latest_row["rsi_14"]) else 50.0
        macd_diff_val = float(latest_row["macd_diff"]) if pd.notna(latest_row["macd_diff"]) else 0.0
        sma20_val = float(latest_row["sma_20"]) if pd.notna(latest_row["sma_20"]) else current_close

        key_signals = []
        if rsi_val > 70:
            key_signals.append("RSI Overbought (>70)")
        elif rsi_val < 30:
            key_signals.append("RSI Oversold (<30)")

        if macd_diff_val > 0:
            key_signals.append("MACD Histogram Positive (Bullish Momentum)")
        else:
            key_signals.append("MACD Histogram Negative (Bearish Momentum)")

        if current_close > sma20_val:
            key_signals.append("Trading Above 20-Day Moving Average")
        else:
            key_signals.append("Trading Below 20-Day Moving Average")

        return {
            "company_id": company_id,
            "company_name": company_name,
            "as_of_date": as_of_date,
            "current_close": round(current_close, 2),
            "predicted_open_price": round(predicted_open_price, 2),
            "expected_gap_pct": gap_pct,
            "gap_type": gap_type,
            "predicted_target_close": round(predicted_target_close, 2),
            "expected_change_pct": price_change_pct,
            "direction": direction,
            "confidence_pct": confidence_pct,
            "prob_bullish": round(prob_up * 100, 1),
            "prob_bearish": round(prob_down * 100, 1),
            "stop_loss": stop_loss,
            "support_20d": support,
            "resistance_20d": resistance,
            "rsi_14": round(rsi_val, 1),
            "key_signals": key_signals
        }

    finally:
        conn.close()


def get_top_forecasts(db_path: str = "nifty100.db", top_n: int = 5) -> dict:
    """
    Evaluates predictions for all companies in nifty100.db and returns top bullish and top bearish stocks.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id FROM companies ORDER BY id").fetchall()
        tickers = [r["id"] for r in rows]
    finally:
        conn.close()

    predictions = []
    for ticker in tickers:
        res = predict_stock_tomorrow(ticker, db_path=db_path)
        if "error" not in res:
            predictions.append(res)

    bullish_list = [p for p in predictions if p["direction"] == "BULLISH"]
    bearish_list = [p for p in predictions if p["direction"] == "BEARISH"]

    bullish_list = sorted(bullish_list, key=lambda x: x["confidence_pct"], reverse=True)[:top_n]
    bearish_list = sorted(bearish_list, key=lambda x: x["confidence_pct"], reverse=True)[:top_n]

    return {
        "top_bullish": bullish_list,
        "top_bearish": bearish_list,
        "total_analyzed": len(predictions)
    }


if __name__ == "__main__":
    logger.info("Testing market predictor module with Next-Day Open Price...")
    sample = predict_stock_tomorrow("RELIANCE")
    print("\n=== RELIANCE PREDICTION ===")
    print(sample)
