import pytest
from typing import Iterator
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_utility_bill_repository
from app.db.in_memory import InMemoryUtilityBillRepository
from app.domain.statuses import UtilityBillStatus
from app.domain.schemas import ValidatedBillResult

# Setup test client and mock repository
test_repo = InMemoryUtilityBillRepository()

def get_test_repo() -> InMemoryUtilityBillRepository:
    return test_repo

@pytest.fixture(autouse=True)
def setup_dependencies() -> Iterator[None]:
    app.dependency_overrides[get_utility_bill_repository] = get_test_repo
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_repo() -> None:
    test_repo.bills = {}

def test_get_dashboard_alerts_empty() -> None:
    response = client.get("/dashboard/alerts?sme_id=test_sme")
    assert response.status_code == 200
    data = response.json()
    assert data["flagged_low_confidence_count"] == 0
    assert data["flagged_unreadable_count"] == 0
    assert data["total_requiring_review"] == 0

def test_get_dashboard_alerts_counts() -> None:
    # 1. Create bills with different statuses
    test_repo.create_pending_utility_bill("test_sme", "url1", "file1.pdf")
    
    # Manually update statuses to simulate processed state
    bill2_id = test_repo.create_pending_utility_bill("test_sme", "url2", "file2.pdf")
    test_repo.update_bill_extraction_result(bill2_id, ValidatedBillResult(
        status=UtilityBillStatus.flagged_low_confidence,
        validation_reasons=["Low confidence"]
    ))
    
    bill3_id = test_repo.create_pending_utility_bill("test_sme", "url3", "file3.pdf")
    test_repo.mark_bill_unreadable(bill3_id, "Corrupt")
    
    response = client.get("/dashboard/alerts?sme_id=test_sme")
    assert response.status_code == 200
    data = response.json()
    assert data["flagged_low_confidence_count"] == 1
    assert data["flagged_unreadable_count"] == 1
    assert data["total_requiring_review"] == 2

def test_get_dashboard_overview() -> None:
    # 1. Success Electricity Bill
    bill1_id = test_repo.create_pending_utility_bill("test_sme", "url1", "file1.pdf")
    test_repo.update_bill_extraction_result(bill1_id, ValidatedBillResult(
        status=UtilityBillStatus.success,
        calculated_co2e=58.0,
        extracted_unit="kWh"
    ))
    
    # 2. Resolved Water Bill
    bill2_id = test_repo.create_pending_utility_bill("test_sme", "url2", "file2.pdf")
    test_repo.update_bill_extraction_result(bill2_id, ValidatedBillResult(
        status=UtilityBillStatus.success, # Will update to resolved manually
        calculated_co2e=10.0,
        extracted_unit="m3"
    ))
    bill2 = test_repo.get_bill(bill2_id)
    if bill2:
        bill2.status = UtilityBillStatus.resolved_by_client
    
    # 3. Pending bill (should be ignored)
    test_repo.create_pending_utility_bill("test_sme", "url3", "file3.pdf")
    
    response = client.get("/dashboard/overview?sme_id=test_sme")
    assert response.status_code == 200
    data = response.json()
    assert data["total_co2e_ytd"] == 68.0
    assert data["electricity_co2e"] == 58.0
    assert data["water_co2e"] == 10.0
