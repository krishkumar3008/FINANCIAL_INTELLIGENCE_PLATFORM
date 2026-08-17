from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_get_sectors_list():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 10


def test_get_sector_companies_valid():
    response = client.get("/api/v1/sectors/Information Technology/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for comp in data:
        assert comp["broad_sector"] == "Information Technology"


def test_get_sector_companies_invalid_404():
    response = client.get("/api/v1/sectors/UNKNOWN_SECTOR_XYZ/companies")
    assert response.status_code == 404
