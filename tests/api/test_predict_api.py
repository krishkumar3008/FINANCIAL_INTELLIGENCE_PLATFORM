import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_predict_ticker_endpoint():
    response = client.get("/api/v1/predict/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "RELIANCE"
    assert "direction" in data
    assert data["direction"] in ["BULLISH", "BEARISH"]
    assert "confidence_pct" in data


def test_predict_invalid_ticker():
    response = client.get("/api/v1/predict/INVALID_TICKER_999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_predict_top_forecasts_endpoint():
    response = client.get("/api/v1/predict/top-forecasts?top_n=3")
    assert response.status_code == 200
    data = response.json()
    assert "top_bullish" in data
    assert "top_bearish" in data
    assert len(data["top_bullish"]) <= 3
    assert len(data["top_bearish"]) <= 3
