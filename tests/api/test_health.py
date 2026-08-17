from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db_row_counts" in data
    counts = data["db_row_counts"]
    expected_tables = [
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
    for table in expected_tables:
        assert table in counts
        assert counts[table] >= 0
