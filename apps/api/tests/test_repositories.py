from app.db.in_memory import InMemorySmeRepository, InMemoryUtilityBillRepository
from app.domain.statuses import UtilityBillStatus
from app.domain.schemas import ValidatedBillResult

def test_sme_repository_email_lookup() -> None:
    repo = InMemorySmeRepository()
    repo.add_plc("plc-1", "Test PLC")
    repo.add_sme("sme-1", "plc-1", "Test SME")
    repo.authorize_email("sme-1", "test@example.com")
    
    # Case insensitive lookup
    sme = repo.find_sme_by_authorized_email("TEST@example.com")
    assert sme is not None
    assert sme["id"] == "sme-1"
    
    # Unknown email
    assert repo.find_sme_by_authorized_email("unknown@example.com") is None

def test_utility_bill_repository_create_and_claim() -> None:
    repo = InMemoryUtilityBillRepository()
    
    # Create
    bill_id = repo.create_pending_utility_bill("sme-1", "s3://bucket/file.pdf", "file.pdf")
    bill = repo.get_bill(bill_id)
    assert bill is not None
    assert bill.status == UtilityBillStatus.pending
    
    # Claim
    claimed = repo.claim_next_pending_bill()
    assert claimed is not None
    assert claimed.id == bill_id
    
    # Cannot claim again
    assert repo.claim_next_pending_bill() is None

def test_utility_bill_repository_updates() -> None:
    repo = InMemoryUtilityBillRepository()
    bill_id = repo.create_pending_utility_bill("sme-1", "s3://bucket/file.pdf", "file.pdf")
    
    # Update extraction result
    result = ValidatedBillResult(
        status=UtilityBillStatus.success,
        calculated_co2e=100.5,
        emission_factor_used=0.58
    )
    repo.update_bill_extraction_result(bill_id, result)
    
    bill = repo.get_bill(bill_id)
    assert bill is not None
    assert bill.status == UtilityBillStatus.success
    assert bill.calculated_co2e == 100.5
    
    # Mark unreadable
    bill_id2 = repo.create_pending_utility_bill("sme-1", "s3://bucket/file2.pdf", "file2.pdf")
    repo.mark_bill_unreadable(bill_id2, "Unreadable PDF")
    bill2 = repo.get_bill(bill_id2)
    assert bill2 is not None
    assert bill2.status == UtilityBillStatus.flagged_unreadable
    assert "Unreadable PDF" in bill2.validation_reasons
    
    # Approve bill
    repo.approve_bill(bill_id2, "reviewer-1", "TNB", "2024-01", 100.0, "kWh", 58.0)
    bill2 = repo.get_bill(bill_id2)
    assert bill2 is not None
    assert bill2.status == UtilityBillStatus.resolved_by_client
    assert bill2.reviewer_id == "reviewer-1"
    assert bill2.calculated_co2e == 58.0
    assert bill2.extracted_provider == "TNB"

def test_utility_bill_repository_metrics() -> None:
    repo = InMemoryUtilityBillRepository()
    
    b1 = repo.create_pending_utility_bill("sme-1", "url1", "file1")
    repo.update_bill_extraction_result(b1, ValidatedBillResult(
        status=UtilityBillStatus.success, calculated_co2e=10.0, emission_factor_used=0.5
    ))
    
    b2 = repo.create_pending_utility_bill("sme-1", "url2", "file2")
    repo.mark_bill_unreadable(b2, "bad")
    
    b3 = repo.create_pending_utility_bill("sme-1", "url3", "file3")
    repo.update_bill_extraction_result(b3, ValidatedBillResult(
        status=UtilityBillStatus.flagged_low_confidence
    ))
    
    alerts_resp = repo.get_dashboard_alerts("sme-1")
    assert alerts_resp.flagged_unreadable_count == 1
    assert alerts_resp.flagged_low_confidence_count == 1
    
    overview_resp = repo.get_dashboard_overview("sme-1")
    assert overview_resp.total_co2e_ytd == 10.0
    
    export = repo.list_bills_for_export()
    assert len(export) == 1
    assert export[0].id == b1
