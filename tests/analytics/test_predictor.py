import pytest
import pandas as pd
from src.analytics.predictor import compute_technical_indicators, predict_stock_tomorrow, get_top_forecasts


def test_compute_technical_indicators():
    data = {
        "date": [f"2026-01-{i+1:02d}" for i in range(40)],
        "open_price": [100.0 + i for i in range(40)],
        "high_price": [105.0 + i for i in range(40)],
        "low_price": [95.0 + i for i in range(40)],
        "close_price": [102.0 + i for i in range(40)],
        "volume": [10000 + (i * 100) for i in range(40)],
    }
    df = pd.DataFrame(data)
    res = compute_technical_indicators(df)

    assert "sma_20" in res.columns
    assert "rsi_14" in res.columns
    assert "macd" in res.columns
    assert "bb_upper" in res.columns
    assert "target_up" in res.columns


def test_predict_stock_tomorrow():
    result = predict_stock_tomorrow("RELIANCE")
    assert "company_id" in result
    assert result["company_id"] == "RELIANCE"
    if "error" not in result:
        assert result["direction"] in ["BULLISH", "BEARISH"]
        assert 0.0 <= result["confidence_pct"] <= 100.0
        assert "predicted_target_close" in result
        assert "stop_loss" in result


def test_get_top_forecasts():
    top_res = get_top_forecasts(top_n=2)
    assert "top_bullish" in top_res
    assert "top_bearish" in top_res
    assert len(top_res["top_bullish"]) <= 2
    assert len(top_res["top_bearish"]) <= 2
