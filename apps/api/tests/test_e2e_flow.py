import pytest
from typing import Iterator
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.core.dependencies import get_utility_bill_repository, get_storage_service, get_current_user_id, get_sme_repository
from app.db.in_memory import InMemoryUtilityBillRepository, InMemorySmeRepository
from app.storage.local_storage import LocalStorageService

# Setup mocks
test_repo = InMemoryUtilityBillRepository()
test_sme_repo = InMemorySmeRepository()
test_storage = MagicMock(spec=LocalStorageService)

def get_test_repo() -> InMemoryUtilityBillRepository:
    return test_repo

def get_test_sme_repo() -> InMemorySmeRepository:
    return test_sme_repo

def get_test_storage() -> MagicMock:
    return test_storage

def get_test_user() -> str:
    return "e2e_reviewer"

@pytest.fixture(autouse=True)
def setup_dependencies() -> Iterator[None]:
    app.dependency_overrides[get_utility_bill_repository] = get_test_repo
    app.dependency_overrides[get_sme_repository] = get_test_sme_repo
    app.dependency_overrides[get_storage_service] = get_test_storage
    app.dependency_overrides[get_current_user_id] = get_test_user
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_state() -> None:
    test_repo.bills = {}
    test_sme_repo.plcs = {"plc1": {"id": "plc1", "name": "Test PLC"}}
    test_sme_repo.smes = {"test_sme": {"id": "test_sme", "plc_id": "plc1", "company_name": "Test SME"}}
    test_sme_repo.authorized_emails = {"test@example.com": "test_sme"}

def test_full_lifecycle_e2e() -> None:
    # 1. Ingestion via Webhook
    webhook_payload = {
        "From": "test@example.com",
        "Attachments": [
            {"Name": "bill.pdf", "Content": "YmFzZTY0X2RhdGE=", "ContentType": "application/pdf"}
        ]
    }
    from app.storage.base import StoredFile
    test_storage.save_raw_attachment.return_value = StoredFile(
        url_or_path="http://storage/bill.pdf",
        content_type="application/pdf",
        size_bytes=100
    )
    
    response = client.post("/webhook/incoming-email", json=webhook_payload)
    assert response.status_code == 200
    assert response.json()["accepted_attachments"] == 1
    
    # Get the bill_id from the repo (it should be the only one)
    bill_id = list(test_repo.bills.keys())[0]
    
    # 2. Check initial state in Dashboard Alerts
    response = client.get("/dashboard/alerts?sme_id=test_sme")
    assert response.status_code == 200
    # Initially pending, so alerts should be 0 (only low_confidence and unreadable count as alerts)
    assert response.json()["total_requiring_review"] == 0
    
    # 3. Simulate processing (Worker logic)
    # We'll manually trigger the state change that the processor would do
    test_repo.mark_bill_unreadable(bill_id, "Mock failure")
    
    # 4. Check Dashboard Alerts again
    response = client.get("/dashboard/alerts?sme_id=test_sme")
    assert response.json()["flagged_unreadable_count"] == 1
    assert response.json()["total_requiring_review"] == 1
    
    # 5. HITL Approval
    approval_payload = {
        "provider": "TNB",
        "billing_period": "2024-01",
        "usage_value": 200.0,
        "usage_unit": "kWh"
    }
    response = client.post(f"/bills/{bill_id}/approve", json=approval_payload)
    assert response.status_code == 200
    
    # 6. Verify Dashboard Overview
    response = client.get("/dashboard/overview?sme_id=test_sme")
    assert response.status_code == 200
    # 200.0 * 0.58 = 116.0
    assert response.json()["total_co2e_ytd"] == 116.0
    assert response.json()["electricity_co2e"] == 116.0
    
    # 7. Verify Alert is cleared
    response = client.get("/dashboard/alerts?sme_id=test_sme")
    assert response.json()["total_requiring_review"] == 0

    # 8. Verify CSV Export
    response = client.get("/exports/csv?sme_id=test_sme")
    assert response.status_code == 200
    # Provider (TNB) is no longer in CSI CSV, but SME Name is.
    assert "Test SME" in response.text
    assert "116.0" in response.text
def test_unauthorized_email_rejection() -> None:
    # Use valid base64 but unauthorized email
    webhook_payload = {
        "From": "hacker@evil.com",
        "Attachments": [{"Name": "virus.pdf", "Content": "YmFzZTY0X2RhdGE=", "ContentType": "application/pdf"}]
    }
    response = client.post("/webhook/incoming-email", json=webhook_payload)
    assert response.status_code == 200 
    assert response.json()["message"] == "unauthorized sender ignored"
    assert len(test_repo.bills) == 0

def test_corrupted_attachment_handling() -> None:
    webhook_payload = {
        "From": "test@example.com",
        "Attachments": [{"Name": "corrupted.pdf", "Content": "YmFzZTY0X2RhdGE=", "ContentType": "application/pdf"}]
    }
    test_storage.save_raw_attachment.return_value = None # Simulate storage failure
    
    response = client.post("/webhook/incoming-email", json=webhook_payload)
    assert response.status_code == 200
    assert response.json()["accepted_attachments"] == 0
