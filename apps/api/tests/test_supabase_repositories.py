import pytest
from unittest.mock import MagicMock
from app.db.supabase_repositories import SupabaseSmeRepository, SupabaseUtilityBillRepository
from app.domain.statuses import UtilityBillStatus
from app.domain.schemas import ValidatedBillResult

from typing import Any, Optional

class MockResponse:
    def __init__(self, data: Optional[list[Any]] = None, count: Optional[int] = None):
        self.data = data or []
        self.count = count

@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    # Mock the fluent chain: client.table("name").select("...").eq("...").execute() -> returns MockResponse
    table_mock = MagicMock()
    client.table.return_value = table_mock
    
    # We will configure specific return values in tests or just let it return MagicMocks that eventually execute
    return client

def test_sme_repository_lookup(mock_client: MagicMock) -> None:
    # Setup mock response
    mock_client.table().select().eq().execute.return_value = MockResponse(
        data=[{"smes": {"id": "sme-123", "plc_id": "plc-123", "company_name": "Test SME"}}]
    )
    
    repo = SupabaseSmeRepository(mock_client)
    sme = repo.find_sme_by_authorized_email("test@example.com")
    
    assert sme is not None
    assert sme["id"] == "sme-123"
    
    # Verify the correct table was called
    mock_client.table.assert_called_with("authorized_emails")

def test_utility_bill_create_pending(mock_client: MagicMock) -> None:
    mock_client.table().insert().execute.return_value = MockResponse(
        data=[{"id": "bill-123"}]
    )
    
    repo = SupabaseUtilityBillRepository(mock_client)
    bill_id = repo.create_pending_utility_bill("sme-123", "s3://test", "file.pdf")
    
    assert bill_id == "bill-123"
    mock_client.table.assert_called_with("utility_bills")
    # Verify payload
    insert_call = mock_client.table().insert.call_args[0][0]
    assert insert_call["sme_id"] == "sme-123"
    assert insert_call["status"] == UtilityBillStatus.pending.value
    assert insert_call["raw_file_url"] == "s3://test"
    assert insert_call["original_filename"] == "file.pdf"

def test_utility_bill_update_extraction(mock_client: MagicMock) -> None:
    repo = SupabaseUtilityBillRepository(mock_client)
    
    result = ValidatedBillResult(
        status=UtilityBillStatus.success,
        calculated_co2e=50.5,
        emission_factor_used=0.58,
        validation_reasons=[]
    )
    
    repo.update_bill_extraction_result("bill-123", result)
    
    mock_client.table.assert_called_with("utility_bills")
    update_call = mock_client.table().update.call_args[0][0]
    
    assert update_call["status"] == UtilityBillStatus.success.value
    assert update_call["calculated_co2e"] == 50.5
    assert update_call["emission_factor_used"] == 0.58
    assert update_call["validation_reasons"] == []

def test_utility_bill_mark_unreadable(mock_client: MagicMock) -> None:
    repo = SupabaseUtilityBillRepository(mock_client)
    repo.mark_bill_unreadable("bill-123", "Blurry")
    
    update_call = mock_client.table().update.call_args[0][0]
    assert update_call["status"] == UtilityBillStatus.flagged_unreadable.value
    assert update_call["validation_reasons"] == ["Blurry"]

def test_utility_bill_approve(mock_client: MagicMock) -> None:
    repo = SupabaseUtilityBillRepository(mock_client)
    repo.approve_bill("bill-123", "reviewer-99", "TNB", "2024-01", 100.0, "kWh", 58.0)
    
    update_call = mock_client.table().update.call_args[0][0]
    assert update_call["status"] == UtilityBillStatus.resolved_by_client.value
    assert update_call["reviewer_id"] == "reviewer-99"
    assert update_call["extracted_provider"] == "TNB"
    assert update_call["extracted_period"] == "2024-01"
    assert update_call["extracted_usage"] == 100.0
    assert update_call["extracted_usage_unit"] == "kWh"
    assert update_call["calculated_co2e"] == 58.0
