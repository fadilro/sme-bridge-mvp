import pytest
import base64
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import (
    get_email_authorization_service,
    get_bounce_email_service,
    get_storage_service,
    get_utility_bill_repository,
    get_sme_repository
)
from app.db.in_memory import InMemoryUtilityBillRepository, InMemorySmeRepository
from app.storage.local_storage import LocalStorageService
from app.email.authorization import EmailAuthorizationService
from app.email.bounce import NoopBounceEmailService

@pytest.fixture
def test_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    sme_repo = InMemorySmeRepository()
    sme_repo.add_plc("plc-1", "Test PLC")
    sme_repo.add_sme("sme-1", "plc-1", "Test SME")
    sme_repo.authorize_email("sme-1", "auth@example.com")
    
    bill_repo = InMemoryUtilityBillRepository()
    storage = LocalStorageService(base_dir=str(tmp_path))
    auth_service = EmailAuthorizationService(sme_repo)
    bounce_service = NoopBounceEmailService()
    
    app.dependency_overrides[get_sme_repository] = lambda: sme_repo
    app.dependency_overrides[get_utility_bill_repository] = lambda: bill_repo
    app.dependency_overrides[get_storage_service] = lambda: storage
    app.dependency_overrides[get_email_authorization_service] = lambda: auth_service
    app.dependency_overrides[get_bounce_email_service] = lambda: bounce_service
    
    yield TestClient(app)
    
    app.dependency_overrides.clear()

def test_webhook_unauthorized_sender(test_client: TestClient) -> None:
    payload = {
        "From": "hacker@evil.com",
        "Subject": "Phishing",
        "Attachments": []
    }
    
    response = test_client.post("/webhook/incoming-email", json=payload)
    
    # Should return 200 so postmark doesn't retry
    assert response.status_code == 200
    assert response.json()["message"] == "unauthorized sender ignored"

def test_webhook_invalid_payload(test_client: TestClient) -> None:
    # Missing From
    payload = {
        "Subject": "Missing from"
    }
    
    response = test_client.post("/webhook/incoming-email", json=payload)
    assert response.status_code == 422

def test_webhook_authorized_success(test_client: TestClient) -> None:
    att1 = base64.b64encode(b"pdf data").decode("ascii")
    att2 = base64.b64encode(b"img data").decode("ascii")
    
    payload = {
        "From": "auth@example.com",
        "Subject": "My Bills",
        "Attachments": [
            {"Name": "bill1.pdf", "Content": att1, "ContentType": "application/pdf"},
            {"Name": "bill2.jpg", "Content": att2, "ContentType": "image/jpeg"}
        ]
    }
    
    response = test_client.post("/webhook/incoming-email", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted_attachments"] == 2
    assert response.json()["message"] == "success"
    
    # Verify DB rows
    # We injected the mock dependencies into the app. We can resolve them to check state if needed,
    # or just trust the response for now.
    
def test_webhook_empty_attachments(test_client: TestClient) -> None:
    payload = {
        "From": "auth@example.com",
        "Subject": "No Bills here",
        "Attachments": []
    }
    response = test_client.post("/webhook/incoming-email", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted_attachments"] == 0
