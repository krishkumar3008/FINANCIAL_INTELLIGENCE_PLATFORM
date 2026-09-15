import json
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


def save_daily_prediction(pred: dict, db_path: str = "nifty100.db") -> bool:
    """Persists a single prediction dictionary to daily_predictions table."""
    if not pred or "error" in pred or not pred.get("as_of_date"):
        return False
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO daily_predictions (
                company_id, prediction_date, current_close, predicted_open_price,
                expected_gap_pct, gap_type, predicted_target_close, expected_change_pct,
                direction, confidence_pct, prob_bullish, prob_bearish,
                stop_loss, support_20d, resistance_20d, rsi_14, key_signals
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_id, prediction_date) DO UPDATE SET
                current_close=excluded.current_close,
                predicted_open_price=excluded.predicted_open_price,
                expected_gap_pct=excluded.expected_gap_pct,
                gap_type=excluded.gap_type,
                predicted_target_close=excluded.predicted_target_close,
                expected_change_pct=excluded.expected_change_pct,
                direction=excluded.direction,
                confidence_pct=excluded.confidence_pct,
                prob_bullish=excluded.prob_bullish,
                prob_bearish=excluded.prob_bearish,
                stop_loss=excluded.stop_loss,
                support_20d=excluded.support_20d,
                resistance_20d=excluded.resistance_20d,
                rsi_14=excluded.rsi_14,
                key_signals=excluded.key_signals,
                created_at=CURRENT_TIMESTAMP
            """,
            (
                pred["company_id"],
                pred["as_of_date"],
                pred.get("current_close", 0.0),
                pred.get("predicted_open_price", 0.0),
                pred.get("expected_gap_pct", 0.0),
                pred.get("gap_type", "FLAT OPEN ⚖️"),
                pred.get("predicted_target_close", 0.0),
                pred.get("expected_change_pct", 0.0),
                pred.get("direction", "BULLISH"),
                pred.get("confidence_pct", 50.0),
                pred.get("prob_bullish", 50.0),
                pred.get("prob_bearish", 50.0),
                pred.get("stop_loss", 0.0),
                pred.get("support_20d", 0.0),
                pred.get("resistance_20d", 0.0),
                pred.get("rsi_14", 50.0),
                json.dumps(pred.get("key_signals", []))
            )
        )
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"Failed to save prediction to database for {pred.get('company_id')}: {e}")
        return False
    finally:
        conn.close()


def get_cached_prediction(company_id: str, db_path: str = "nifty100.db") -> dict | None:
    """
    Retrieves pre-computed prediction from daily_predictions table if it matches
    the latest available stock price date for that company.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        p_row = cursor.execute("SELECT MAX(date) as max_d FROM stock_prices WHERE company_id=?", (company_id,)).fetchone()
        latest_price_date = p_row["max_d"] if p_row and p_row["max_d"] else None
        if not latest_price_date:
            return None

        row = cursor.execute(
            """
            SELECT dp.*, c.company_name
            FROM daily_predictions dp
            LEFT JOIN companies c ON dp.company_id = c.id
            WHERE dp.company_id=? AND dp.prediction_date=?
            """,
            (company_id, latest_price_date)
        ).fetchone()

        if not row:
            return None

        key_signals = []
        if row["key_signals"]:
            try:
                key_signals = json.loads(row["key_signals"])
            except Exception:
                key_signals = []

        return {
            "company_id": row["company_id"],
            "company_name": row["company_name"] or row["company_id"],
            "as_of_date": row["prediction_date"],
            "current_close": row["current_close"],
            "predicted_open_price": row["predicted_open_price"],
            "expected_gap_pct": row["expected_gap_pct"],
            "gap_type": row["gap_type"],
            "predicted_target_close": row["predicted_target_close"],
            "expected_change_pct": row["expected_change_pct"],
            "direction": row["direction"],
            "confidence_pct": row["confidence_pct"],
            "prob_bullish": row["prob_bullish"],
            "prob_bearish": row["prob_bearish"],
            "stop_loss": row["stop_loss"],
            "support_20d": row["support_20d"],
            "resistance_20d": row["resistance_20d"],
            "rsi_14": row["rsi_14"],
            "key_signals": key_signals,
            "cached": True
        }
    except Exception as e:
        logger.warning(f"Error querying cached prediction for {company_id}: {e}")
        return None
    finally:
        conn.close()


def get_cached_top_forecasts(db_path: str = "nifty100.db", top_n: int = 5) -> dict | None:
    """
    Retrieves pre-computed top forecasts across companies from daily_predictions
    if data matches the latest stock price date.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        max_row = cursor.execute("SELECT MAX(prediction_date) as max_d, COUNT(*) as cnt FROM daily_predictions").fetchone()
        if not max_row or not max_row["max_d"] or max_row["cnt"] < 10:
            return None

        sp_row = cursor.execute("SELECT MAX(date) as max_d FROM stock_prices").fetchone()
        if sp_row and sp_row["max_d"] and sp_row["max_d"] != max_row["max_d"]:
            return None

        latest_date = max_row["max_d"]
        rows = cursor.execute(
            """
            SELECT dp.*, c.company_name
            FROM daily_predictions dp
            LEFT JOIN companies c ON dp.company_id = c.id
            WHERE dp.prediction_date=?
            """,
            (latest_date,)
        ).fetchall()

        if not rows or len(rows) < 10:
            return None

        predictions = []
        for r in rows:
            try:
                sig = json.loads(r["key_signals"]) if r["key_signals"] else []
            except Exception:
                sig = []
            predictions.append({
                "company_id": r["company_id"],
                "company_name": r["company_name"] or r["company_id"],
                "as_of_date": r["prediction_date"],
                "current_close": r["current_close"],
                "predicted_open_price": r["predicted_open_price"],
                "expected_gap_pct": r["expected_gap_pct"],
                "gap_type": r["gap_type"],
                "predicted_target_close": r["predicted_target_close"],
                "expected_change_pct": r["expected_change_pct"],
                "direction": r["direction"],
                "confidence_pct": r["confidence_pct"],
                "prob_bullish": r["prob_bullish"],
                "prob_bearish": r["prob_bearish"],
                "stop_loss": r["stop_loss"],
                "support_20d": r["support_20d"],
                "resistance_20d": r["resistance_20d"],
                "rsi_14": r["rsi_14"],
                "key_signals": sig,
                "cached": True
            })

        bullish_list = [p for p in predictions if p["direction"] == "BULLISH"]
        bearish_list = [p for p in predictions if p["direction"] == "BEARISH"]

        bullish_list = sorted(bullish_list, key=lambda x: x["confidence_pct"], reverse=True)[:top_n]
        bearish_list = sorted(bearish_list, key=lambda x: x["confidence_pct"], reverse=True)[:top_n]

        return {
            "top_bullish": bullish_list,
            "top_bearish": bearish_list,
            "total_analyzed": len(predictions),
            "cached": True
        }
    except Exception as e:
        logger.warning(f"Error querying cached top forecasts: {e}")
        return None
    finally:
        conn.close()


def predict_stock_tomorrow(company_id: str, db_path: str = "nifty100.db", force_train: bool = False) -> dict:
    """
    Trains ML models on historical prices for company_id and returns next-day market forecast
    including Opening Price Forecast, Closing Price Target, and Directional Signals.
    Checks and returns pre-computed cached predictions when available unless force_train=True.
    """
    if not force_train:
        cached = get_cached_prediction(company_id, db_path=db_path)
        if cached:
            return cached

    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        comp_row = cursor.execute("SELECT company_name FROM companies WHERE id=?", (company_id,)).fetchone()
        company_name = comp_row["company_name"] if comp_row else company_id

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

        clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        clf.fit(X, y_cls)

        reg_close = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        reg_close.fit(X, y_reg_close)

        reg_open = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        reg_open.fit(X, y_reg_open)

        latest_row = df.iloc[-1]
        latest_features = latest_row[FEATURE_COLS].to_frame().T.apply(pd.to_numeric, errors='coerce').fillna(0.0)

        prob_up = float(clf.predict_proba(latest_features)[0][1])
        prob_down = 1.0 - prob_up

        predicted_target_close = float(reg_close.predict(latest_features)[0])
        predicted_open_price = float(reg_open.predict(latest_features)[0])

        current_close = float(latest_row["close_price"])
        as_of_date = str(latest_row["date"])

        direction = "BULLISH" if prob_up >= 0.50 else "BEARISH"
        confidence_pct = round((prob_up if direction == "BULLISH" else prob_down) * 100, 1)

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

        result = {
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

        # Auto-cache this prediction
        save_daily_prediction(result, db_path=db_path)
        return result

    finally:
        conn.close()


def get_top_forecasts(db_path: str = "nifty100.db", top_n: int = 5, force_refresh: bool = False) -> dict:
    """
    Evaluates predictions for all companies in nifty100.db and returns top bullish and top bearish stocks.
    Uses pre-computed cache for instant execution if available and fresh.
    """
    if not force_refresh:
        cached = get_cached_top_forecasts(db_path=db_path, top_n=top_n)
        if cached:
            return cached

    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id FROM companies ORDER BY id").fetchall()
        tickers = [r["id"] for r in rows]
    finally:
        conn.close()

    predictions = []
    for ticker in tickers:
        res = predict_stock_tomorrow(ticker, db_path=db_path, force_train=False)
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


def batch_generate_and_save_predictions(db_path: str = "nifty100.db") -> dict:
    """
    Generates and saves next-day market predictions for all 92 Nifty 100 companies.
    Intended for execution during the daily market close pipeline.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id FROM companies ORDER BY id").fetchall()
        tickers = [r["id"] for r in rows]
    finally:
        conn.close()

    logger.info(f"Starting batch prediction generation for {len(tickers)} companies...")
    saved_count = 0
    errors = []

    for ticker in tickers:
        try:
            pred = predict_stock_tomorrow(ticker, db_path=db_path, force_train=True)
            if "error" in pred:
                errors.append(f"{ticker}: {pred['error']}")
            else:
                saved = save_daily_prediction(pred, db_path=db_path)
                if saved:
                    saved_count += 1
        except Exception as e:
            errors.append(f"{ticker}: {str(e)}")

    logger.info(f"Batch prediction complete. Successfully saved {saved_count}/{len(tickers)} companies.")
    return {
        "total_companies": len(tickers),
        "saved_count": saved_count,
        "errors_count": len(errors),
        "errors": errors[:10]
    }


if __name__ == "__main__":
    logger.info("Testing market predictor module with Next-Day Open Price...")
    sample = predict_stock_tomorrow("RELIANCE")
    print("\n=== RELIANCE PREDICTION ===")
    print(sample)
