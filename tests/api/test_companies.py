from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_get_companies_list():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 92


def test_get_company_tcs():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "TCS"
    assert "company_name" in data
    assert "latest_kpis" in data


def test_get_company_invalid():
    response = client.get("/api/v1/companies/NONEXISTENT_TICKER_99")
    assert response.status_code == 404


def test_get_company_pl_history():
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5


def test_get_company_ratios():
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5


def test_get_company_tearsheet_pdf():
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) >= 30000
