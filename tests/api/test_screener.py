from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_screener_valid_filter():
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for comp in data:
        assert comp["roe_pct"] >= 15.0


def test_screener_invalid_param_400():
    response = client.get("/api/v1/screener?max_de=-5")
    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "max_de" in detail or "negative" in detail


def test_screener_sector_filter():
    response = client.get("/api/v1/screener?sector=Information Technology")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for comp in data:
        assert comp["broad_sector"] == "Information Technology"
