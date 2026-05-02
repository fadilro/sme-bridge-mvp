import logging
import argparse
from typing import Protocol
from app.db.repositories import UtilityBillRepository
from app.core.config import get_settings
from app.db.supabase_client import create_supabase_client
from app.db.supabase_repositories import SupabaseUtilityBillRepository
from app.storage.local_storage import LocalStorageService
from app.storage.supabase_storage import SupabaseStorageService
from app.processing.llm_client import OllamaGemmaClient, FakeLLMClient
from app.processing.processor import UtilityBillProcessor
from app.domain.statuses import UtilityBillStatus
from app.domain.schemas import ValidatedBillResult

logger = logging.getLogger(__name__)

class BillProcessor(Protocol):
    def process(self, bill_id: str, sme_id: str) -> None:
        """
        Process a specific utility bill.
        Implementations should handle extraction and data mapping.
        """
        ...

class FakeBillProcessor(BillProcessor):
    """
    Dummy processor for Milestone 11.
    """
    def __init__(self, repo: UtilityBillRepository):
        self.repo = repo

    def process(self, bill_id: str, sme_id: str) -> None:
        logger.info(f"Fake processor executing for bill {bill_id} (SME: {sme_id})")
        # Just transition it to success
        result = ValidatedBillResult(
            status=UtilityBillStatus.success,
            calculated_co2e=100.0,
            emission_factor_used=0.5,
            validation_reasons=[]
        )
        self.repo.update_bill_extraction_result(bill_id, result)
        logger.info(f"Fake processor finished for bill {bill_id}")


class ProcessingWorker:
    def __init__(self, repo: UtilityBillRepository, processor: BillProcessor):
        self.repo = repo
        self.processor = processor

    def process_one(self) -> bool:
        """
        Claims and processes exactly one pending bill.
        Returns True if a bill was processed, False if queue is empty.
        """
        bill = self.repo.claim_next_pending_bill()
        if not bill:
            return False
            
        bill_id = bill.id
        sme_id = bill.sme_id
        
        logger.info(f"Claimed pending bill {bill_id} for processing.")
        
        try:
            self.processor.process(bill_id, sme_id)
            return True
        except Exception as e:
            logger.error(f"Error processing bill {bill_id}: {e}")
            try:
                self.repo.mark_bill_unreadable(bill_id, str(e))
            except Exception as inner_e:
                logger.error(f"Failed to transition bill {bill_id} to unreadable state: {inner_e}")
            return True # True because we did attempt to process a bill, meaning queue had items

    def process_until_empty(self, max_items: int | None = None) -> int:
        """
        Continues processing bills until the queue is empty or max_items is reached.
        Returns the total number of bills processed.
        """
        processed_count = 0
        while True:
            if max_items is not None and processed_count >= max_items:
                break
                
            has_more = self.process_one()
            if not has_more:
                break
                
            processed_count += 1
            
        return processed_count

def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Run the Utility Bill Processing Worker")
    parser.add_argument("--once", action="store_true", help="Process exactly one bill and exit")
    parser.add_argument("--max-items", type=int, default=None, help="Maximum number of bills to process")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    settings = get_settings()
    client = create_supabase_client(settings)
    repo = SupabaseUtilityBillRepository(client)
    
    if settings.APP_ENV == "test" or settings.APP_ENV == "development" and not settings.OLLAMA_BASE_URL:
        # Use local/fake dependencies in test environments
        storage = LocalStorageService(settings.SUPABASE_STORAGE_BUCKET)
        llm_client = FakeLLMClient()
    else:
        # Real dependencies for production/CLI run
        storage = SupabaseStorageService(client)
        llm_client = OllamaGemmaClient(settings.OLLAMA_BASE_URL, settings.GEMMA_MODEL_NAME)
    
    processor = UtilityBillProcessor(
        repo=repo,
        storage=storage,
        llm_client=llm_client,
        emission_factor=settings.EMISSION_FACTOR_ELECTRICITY_KWH
    )
    
    worker = ProcessingWorker(repo, processor)
    
    if args.once:
        logger.info("Running worker in --once mode.")
        worker.process_one()
    else:
        logger.info(f"Running worker with --max-items={args.max_items}")
        count = worker.process_until_empty(max_items=args.max_items)
        logger.info(f"Worker finished. Processed {count} bills.")

if __name__ == "__main__":
    run_cli()
