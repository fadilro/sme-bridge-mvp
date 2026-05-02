import logging
from typing import List, Optional
from app.db.repositories import UtilityBillRepository
from app.storage.base import StorageService
from app.processing.llm_client import LLMClient
from app.processing.file_loader import load_raw_file
from app.processing.pdf_converter import file_to_page_images
from app.processing.image_preprocessor import preprocess_page_image, encode_image_to_png
from app.processing.llm_prompt import build_bill_extraction_prompt
from app.processing.extraction_parser import parse_llm_extraction, aggregate_page_extractions, ExtractedBillData
from app.processing.gpu import clear_gpu_cache
from app.processing.errors import UnreadableFileError, ProcessingError, LLMInferenceError
from app.domain.schemas import ValidatedBillResult
from app.domain.statuses import UtilityBillStatus

logger = logging.getLogger(__name__)

class UtilityBillProcessor:
    """
    Orchestrates the end-to-end processing of a utility bill:
    Loader -> Converter -> Preprocessor -> LLM -> Parser -> Aggregator -> CO2e Calc -> DB Update.
    """
    def __init__(
        self,
        repo: UtilityBillRepository,
        storage: StorageService,
        llm_client: LLMClient,
        emission_factor: float = 0.58  # Default for Malaysia electricity (tCO2e/MWh or kgCO2e/kWh)
    ):
        self.repo = repo
        self.storage = storage
        self.llm_client = llm_client
        self.emission_factor = emission_factor

    def process(self, bill_id: str, sme_id: str) -> None:
        """
        Executes the full processing pipeline for a single bill.
        """
        logger.info(f"Starting processing for bill {bill_id} (SME: {sme_id})")
        
        # 1. Retrieve bill record
        bill_record = self.repo.get_bill(bill_id)
        if not bill_record:
            logger.error(f"Bill {bill_id} not found in repository.")
            return

        try:
            # 2. Load raw file
            data = load_raw_file(self.storage, bill_record.raw_file_url)
            
            # 3. Convert to images
            page_images = file_to_page_images(
                bill_record.original_filename or "bill.pdf",
                "application/octet-stream", # We detect from extension inside converter
                data
            )
            
            # 4. Process each page through LLM
            extractions: List[Optional[ExtractedBillData]] = []
            prompt = build_bill_extraction_prompt()
            
            for i, img in enumerate(page_images):
                logger.info(f"Processing page {i+1}/{len(page_images)} for bill {bill_id}")
                
                # Preprocess & Encode
                processed_img = preprocess_page_image(img)
                png_bytes = encode_image_to_png(processed_img)
                
                # LLM Call
                try:
                    raw_llm_text = self.llm_client.extract_bill_data(png_bytes, prompt)
                    extraction = parse_llm_extraction(raw_llm_text)
                    extractions.append(extraction)
                except (ProcessingError, LLMInferenceError) as e:
                    logger.warning(f"LLM extraction failed for page {i+1} of bill {bill_id}: {e}")
                    extractions.append(None)
                
                # Clear GPU cache after each page to prevent OOM
                clear_gpu_cache()
            
            # 5. Aggregate results
            final_extraction = aggregate_page_extractions(extractions)
            
            if not final_extraction:
                raise UnreadableFileError("No valid extraction data found across all pages.")

            # 6. Final Validation & State Transition
            # Calculate CO2e
            # Assumes usage_value is in kWh (common for electricity)
            co2e = final_extraction.usage_value * self.emission_factor
            
            # Determine status based on confidence
            if final_extraction.confidence.lower() == "high":
                status = UtilityBillStatus.success
                reasons = []
            else:
                status = UtilityBillStatus.flagged_low_confidence
                reasons = ["LLM reported low confidence in extraction."]

            # 7. Update Repository
            result = ValidatedBillResult(
                status=status,
                calculated_co2e=round(co2e, 4),
                emission_factor_used=self.emission_factor,
                validation_reasons=reasons,
                extracted_provider=final_extraction.provider,
                extracted_period=final_extraction.billing_period,
                extracted_usage=final_extraction.usage_value,
                extracted_unit=final_extraction.usage_unit
            )
            self.repo.update_bill_extraction_result(bill_id, result)
            logger.info(f"Processing complete for bill {bill_id}. Status: {status}")

        except UnreadableFileError as e:
            logger.error(f"Bill {bill_id} marked unreadable: {e}")
            self.repo.mark_bill_unreadable(bill_id, str(e))
        except Exception as e:
            logger.error(f"Unexpected error processing bill {bill_id}: {e}")
            clear_gpu_cache()
            self.repo.mark_bill_unreadable(bill_id, f"Unexpected processing error: {e}")
