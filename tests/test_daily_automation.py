import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.database import get_db_connection
from src.analytics.predictor import (
    predict_stock_tomorrow,
    get_top_forecasts,
    get_cached_prediction,
    get_cached_top_forecasts,
)
from src.automation.daily_pipeline import (
    is_market_day,
    get_next_scheduled_run_time,
    get_scheduler_status,
)

client = TestClient(app)


def test_is_market_day():
    import datetime
    # Monday = 0, Friday = 4
    monday = datetime.date(2026, 9, 7)
    sunday = datetime.date(2026, 9, 6)
    assert is_market_day(monday) is True
    assert is_market_day(sunday) is False


def test_get_next_scheduled_run_time():
    next_dt = get_next_scheduled_run_time(16, 0)
    assert next_dt is not None
    assert is_market_day(next_dt.date()) is True
    assert next_dt.hour == 16
    assert next_dt.minute == 0


def test_get_scheduler_status_function():
    status = get_scheduler_status()
    assert "is_market_day_today" in status
    assert "next_scheduled_run" in status
    assert "schedule_window" in status
    assert "total_cached_predictions" in status
    assert status["total_cached_predictions"] >= 90


def test_cached_prediction_retrieval():
    # RELIANCE was pre-computed and saved in daily_predictions
    cached = get_cached_prediction("RELIANCE")
    assert cached is not None
    assert cached["company_id"] == "RELIANCE"
    assert cached.get("cached") is True
    assert "predicted_open_price" in cached
    assert "predicted_target_close" in cached
    assert "direction" in cached


def test_cached_top_forecasts():
    top = get_cached_top_forecasts(top_n=3)
    assert top is not None
    assert "top_bullish" in top
    assert "top_bearish" in top
    assert len(top["top_bullish"]) <= 3
    assert len(top["top_bearish"]) <= 3
    assert top.get("cached") is True


def test_api_scheduler_status_endpoint():
    response = client.get("/api/v1/predict/scheduler/status")
    assert response.status_code == 200
    data = response.json()
    assert "next_scheduled_run" in data
    assert "schedule_window" in data
    assert "total_cached_predictions" in data


def test_database_daily_predictions_table():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cnt = cursor.execute("SELECT COUNT(*) FROM daily_predictions").fetchone()[0]
        assert cnt >= 90

        sample = cursor.execute(
            "SELECT company_id, prediction_date, direction, confidence_pct FROM daily_predictions LIMIT 1"
        ).fetchone()
        assert sample is not None
        assert sample["direction"] in ["BULLISH", "BEARISH"]
        assert sample["confidence_pct"] >= 0.0
    finally:
        conn.close()


def test_database_scheduler_run_log_table():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        log_cnt = cursor.execute("SELECT COUNT(*) FROM scheduler_run_log").fetchone()[0]
        assert log_cnt >= 1

        latest_log = cursor.execute(
            "SELECT status, records_updated, predictions_generated FROM scheduler_run_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert latest_log is not None
        assert latest_log["status"] in ["SUCCESS", "RUNNING", "FAILED"]
    finally:
        conn.close()
