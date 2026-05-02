from app.db.in_memory import InMemoryUtilityBillRepository
from app.processing.worker import ProcessingWorker, BillProcessor
from app.domain.statuses import UtilityBillStatus
from app.domain.schemas import ValidatedBillResult

class ThrowingFakeProcessor(BillProcessor):
    def __init__(self, repo: InMemoryUtilityBillRepository):
        self.repo = repo
        
    def process(self, bill_id: str, sme_id: str) -> None:
        raise ValueError("Intentional processor failure")

class FakeProcessor(BillProcessor):
    def __init__(self, repo: InMemoryUtilityBillRepository):
        self.repo = repo
        self.processed: list[str] = []
        
    def process(self, bill_id: str, sme_id: str) -> None:
        self.processed.append(bill_id)
        result = ValidatedBillResult(
            status=UtilityBillStatus.success,
            calculated_co2e=100.0,
            emission_factor_used=0.5,
            validation_reasons=[]
        )
        self.repo.update_bill_extraction_result(bill_id, result)

def test_worker_empty_queue() -> None:
    repo = InMemoryUtilityBillRepository()
    processor = FakeProcessor(repo)
    worker = ProcessingWorker(repo, processor)
    
    assert worker.process_one() is False

def test_worker_process_one() -> None:
    repo = InMemoryUtilityBillRepository()
    bill = repo.create_pending_utility_bill("sme1", "http://test.com/file", "test.pdf")
    
    processor = FakeProcessor(repo)
    worker = ProcessingWorker(repo, processor)
    
    assert worker.process_one() is True
    assert len(processor.processed) == 1
    assert processor.processed[0] == bill
    
    updated_bill = repo.get_bill(bill)
    assert updated_bill and updated_bill.status == UtilityBillStatus.success

def test_worker_process_until_empty() -> None:
    repo = InMemoryUtilityBillRepository()
    repo.create_pending_utility_bill("sme1", "url1", "1.pdf")
    repo.create_pending_utility_bill("sme1", "url2", "2.pdf")
    repo.create_pending_utility_bill("sme1", "url3", "3.pdf")
    
    processor = FakeProcessor(repo)
    worker = ProcessingWorker(repo, processor)
    
    # Process max 2
    count = worker.process_until_empty(max_items=2)
    assert count == 2
    assert len(processor.processed) == 2
    
    # Process the rest
    count = worker.process_until_empty()
    assert count == 1
    assert len(processor.processed) == 3

def test_worker_processor_exception_handled() -> None:
    repo = InMemoryUtilityBillRepository()
    bill = repo.create_pending_utility_bill("sme1", "url1", "1.pdf")
    
    processor = ThrowingFakeProcessor(repo)
    worker = ProcessingWorker(repo, processor)
    
    # Should return True because a bill was pulled from the queue, even if processing failed.
    # It shouldn't raise the exception to the caller.
    assert worker.process_one() is True
    
    updated_bill = repo.get_bill(bill)
    assert updated_bill and updated_bill.status == UtilityBillStatus.flagged_unreadable
