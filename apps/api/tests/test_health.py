from fastapi.testclient import TestClient
from app.main import create_app

def test_app_factory_can_be_imported_without_credentials() -> None:
    app = create_app()
    assert app.title == "SME Bridge MVP API"

def test_health_returns_200_and_expected_json() -> None:
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "sme-bridge-api"
    }
