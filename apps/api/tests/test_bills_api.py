import pytest
from typing import Iterator
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_utility_bill_repository, get_current_user_id
from app.db.in_memory import InMemoryUtilityBillRepository
from app.domain.statuses import UtilityBillStatus

# Setup test client and mock repository
test_repo = InMemoryUtilityBillRepository()

def get_test_repo() -> InMemoryUtilityBillRepository:
    return test_repo

def get_test_user() -> str:
    return "test_reviewer"

@pytest.fixture(autouse=True)
def setup_dependencies() -> Iterator[None]:
    app.dependency_overrides[get_utility_bill_repository] = get_test_repo
    app.dependency_overrides[get_current_user_id] = get_test_user
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_repo() -> None:
    test_repo.bills = {}

def test_get_bill_detail_404() -> None:
    response = client.get("/bills/non_existent")
    assert response.status_code == 404

def test_get_bill_detail_success() -> None:
    bill_id = test_repo.create_pending_utility_bill("test_sme", "url1", "file1.pdf")
    response = client.get(f"/bills/{bill_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == bill_id
    assert data["status"] == "pending"

def test_approve_bill_success() -> None:
    bill_id = test_repo.create_pending_utility_bill("test_sme", "url1", "file1.pdf")
    
    response = client.post(
        f"/bills/{bill_id}/approve",
        json={
            "provider": "TNB",
            "billing_period": "2024-01",
            "usage_value": 100.0,
            "usage_unit": "kWh"
        }
    )
    assert response.status_code == 200
    
    # Verify DB state
    bill = test_repo.get_bill(bill_id)
    assert bill is not None
    assert bill.status == UtilityBillStatus.resolved_by_client
    # 100.0 * 0.58 (default test factor) = 58.0
    assert bill.calculated_co2e == 58.0
    assert bill.reviewer_id == "test_reviewer"
    assert bill.extracted_provider == "TNB"
