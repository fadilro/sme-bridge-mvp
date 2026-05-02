from unittest.mock import patch
import io
from typing import Any
from PIL import Image
from app.db.in_memory import InMemoryUtilityBillRepository
from app.storage.local_storage import LocalStorageService
from app.processing.llm_client import FakeLLMClient
from app.processing.processor import UtilityBillProcessor
from app.domain.statuses import UtilityBillStatus

def create_dummy_image() -> bytes:
    img = Image.new('RGB', (100, 100), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_processor_success_path(tmp_path: Any) -> None:
    # 1. Setup Dependencies
    repo = InMemoryUtilityBillRepository()
    storage = LocalStorageService(str(tmp_path))
    
    # Pre-populate storage with a "file"
    file_content = create_dummy_image()
    stored_file = storage.save_raw_attachment("test_sme", "bill1", "bill.png", "image/png", file_content)
    raw_file_url = stored_file.url_or_path
    
    # Create DB record
    bill_id = repo.create_pending_utility_bill("test_sme", raw_file_url, "bill.png")
    
    # Mock LLM Response
    llm_response = '{"provider": "TNB", "usage_value": 100.0, "usage_unit": "kWh", "confidence": "high"}'
    llm_client = FakeLLMClient([llm_response])
    
    # 2. Execute Processor
    with patch("app.processing.processor.clear_gpu_cache") as mock_clear:
        processor = UtilityBillProcessor(repo, storage, llm_client, emission_factor=0.5)
        processor.process(bill_id, "test_sme")
        
        # Verify GPU cleanup was called (once per page, dummy image is 1 page)
        assert mock_clear.call_count == 1
    updated_bill = repo.get_bill(bill_id)
    assert updated_bill is not None
    assert updated_bill.status == UtilityBillStatus.success
    assert updated_bill.calculated_co2e == 50.0 # 100 * 0.5
    assert updated_bill.extracted_provider == "TNB"
    assert updated_bill.extracted_usage == 100.0

def test_processor_low_confidence_path(tmp_path: Any) -> None:
    repo = InMemoryUtilityBillRepository()
    storage = LocalStorageService(str(tmp_path))
    file_content = create_dummy_image()
    stored_file = storage.save_raw_attachment("test_sme", "bill2", "bill.png", "image/png", file_content)
    raw_file_url = stored_file.url_or_path
    bill_id = repo.create_pending_utility_bill("test_sme", raw_file_url, "bill.png")
    
    # Low confidence response
    llm_response = '{"provider": "TNB", "usage_value": 100.0, "usage_unit": "kWh", "confidence": "low"}'
    llm_client = FakeLLMClient([llm_response])
    
    processor = UtilityBillProcessor(repo, storage, llm_client, emission_factor=0.5)
    processor.process(bill_id, "test_sme")
    
    updated_bill = repo.get_bill(bill_id)
    assert updated_bill is not None
    assert updated_bill.status == UtilityBillStatus.flagged_low_confidence

def test_processor_unreadable_path(tmp_path: Any) -> None:
    repo = InMemoryUtilityBillRepository()
    storage = LocalStorageService(str(tmp_path))
    # No file in storage!
    bill_id = repo.create_pending_utility_bill("test_sme", "non_existent_url", "bill.png")
    
    llm_client = FakeLLMClient([]) # Should not even be called
    
    processor = UtilityBillProcessor(repo, storage, llm_client)
    processor.process(bill_id, "test_sme")
    
    updated_bill = repo.get_bill(bill_id)
    assert updated_bill is not None
    assert updated_bill.status == UtilityBillStatus.flagged_unreadable
    assert "not found" in updated_bill.validation_reasons[0].lower()

def test_processor_corrupted_image(tmp_path: Any) -> None:
    repo = InMemoryUtilityBillRepository()
    storage = LocalStorageService(str(tmp_path))
    # Write garbage content as "PNG"
    stored_file = storage.save_raw_attachment("test_sme", "bill3", "corrupt.png", "image/png", b"this is not a valid image")
    bill_id = repo.create_pending_utility_bill("test_sme", stored_file.url_or_path, "corrupt.png")
    
    llm_client = FakeLLMClient([]) # Should not be called
    processor = UtilityBillProcessor(repo, storage, llm_client)
    
    processor.process(bill_id, "test_sme")
    
    updated_bill = repo.get_bill(bill_id)
    assert updated_bill.status == UtilityBillStatus.flagged_unreadable
    assert "corrupt" in updated_bill.validation_reasons[0].lower() or "unsupported" in updated_bill.validation_reasons[0].lower()

def test_processor_unsupported_file(tmp_path: Any) -> None:
    repo = InMemoryUtilityBillRepository()
    storage = LocalStorageService(str(tmp_path))
    # Zip file is unsupported
    stored_file = storage.save_raw_attachment("test_sme", "bill4", "test.zip", "application/zip", b"PK...")
    bill_id = repo.create_pending_utility_bill("test_sme", stored_file.url_or_path, "test.zip")
    
    llm_client = FakeLLMClient([])
    processor = UtilityBillProcessor(repo, storage, llm_client)
    
    processor.process(bill_id, "test_sme")
    
    updated_bill = repo.get_bill(bill_id)
    assert updated_bill.status == UtilityBillStatus.flagged_unreadable
    assert "unsupported" in updated_bill.validation_reasons[0].lower()

def test_processor_simulated_oom(tmp_path: Any) -> None:
    repo = InMemoryUtilityBillRepository()
    storage = LocalStorageService(str(tmp_path))
    file_content = create_dummy_image()
    stored_file = storage.save_raw_attachment("test_sme", "bill5", "bill.png", "image/png", file_content)
    bill_id = repo.create_pending_utility_bill("test_sme", stored_file.url_or_path, "bill.png")
    
    class OOMClient(FakeLLMClient):
        def extract_bill_data(self, *args, **kwargs):
            raise RuntimeError("CUDA out of memory")

    llm_client = OOMClient([])
    
    with patch("app.processing.processor.clear_gpu_cache") as mock_clear:
        processor = UtilityBillProcessor(repo, storage, llm_client)
        processor.process(bill_id, "test_sme")
        
        # Verify clear_gpu_cache was called on failure
        # Once for the initial page, once on OOM catch (if processor is built that way)
        # Actually UtilityBillProcessor calls it at the end of each page.
        # If OOM happens, we expect it to be caught and status updated.
        assert mock_clear.called
        
    updated_bill = repo.get_bill(bill_id)
    assert updated_bill.status == UtilityBillStatus.flagged_unreadable
    assert "memory" in updated_bill.validation_reasons[0].lower() or "oom" in updated_bill.validation_reasons[0].lower()
