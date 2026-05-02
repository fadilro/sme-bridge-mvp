from unittest.mock import MagicMock
from app.processing.worker import ProcessingWorker, BillProcessor
from app.db.in_memory import InMemoryUtilityBillRepository
from app.domain.statuses import UtilityBillStatus

def test_worker_continues_after_processor_crash() -> None:
    # 1. Setup Repo with 2 bills
    repo = InMemoryUtilityBillRepository()
    bill1_id = repo.create_pending_utility_bill("sme1", "url1", "file1.pdf")
    bill2_id = repo.create_pending_utility_bill("sme1", "url2", "file2.pdf")
    
    # 2. Setup Mock Processor that crashes on bill1 but succeeds on bill2
    mock_processor = MagicMock(spec=BillProcessor)
    
    def side_effect(bill_id: str, sme_id: str) -> None:
        if bill_id == bill1_id:
            raise RuntimeError("Crashed on bill 1")
        return None
        
    mock_processor.process.side_effect = side_effect
    
    worker = ProcessingWorker(repo, mock_processor)
    
    # 3. Process First Bill (should catch crash and mark unreadable)
    has_more = worker.process_one()
    assert has_more is True
    
    bill1 = repo.get_bill(bill1_id)
    assert bill1 is not None
    assert bill1.status == UtilityBillStatus.flagged_unreadable
    assert "Crashed on bill 1" in bill1.validation_reasons[0]
    
    # 4. Process Second Bill (should still work!)
    has_more = worker.process_one()
    assert has_more is True
    
    assert mock_processor.process.call_count == 2
    # Verify second call was indeed for bill2
    mock_processor.process.assert_any_call(bill2_id, "sme1")
