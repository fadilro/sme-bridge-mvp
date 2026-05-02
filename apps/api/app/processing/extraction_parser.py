import json
import logging
import re
from typing import Optional, List
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class ExtractedBillData(BaseModel):
    provider: Optional[str] = None
    billing_period: Optional[str] = None
    usage_value: float
    usage_unit: str
    confidence: str # 'high' or 'low'

def parse_llm_extraction(raw_text: str) -> Optional[ExtractedBillData]:
    """
    Parses the raw text response from the LLM into an ExtractedBillData object.
    Supports JSON inside markdown code fences.
    """
    # 1. Clean up markdown code fences if present
    # Matches ```json { ... } ``` or just ``` { ... } ```
    clean_text = raw_text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
    if match:
        clean_text = match.group(1)
    
    # 2. Attempt JSON parse
    try:
        data = json.loads(clean_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from LLM response: {e}\nRaw text: {raw_text}")
        return None
        
    # 3. Validate with Pydantic
    try:
        return ExtractedBillData(**data)
    except ValidationError as e:
        logger.error(f"Validation error for LLM response: {e}")
        return None

def aggregate_page_extractions(extractions: List[Optional[ExtractedBillData]]) -> Optional[ExtractedBillData]:
    """
    Aggregates results from multiple pages, preferring the 'best' extraction.
    Criteria:
    1. Confidence ('high' preferred over 'low')
    2. Presence of provider name
    3. Positive usage value
    """
    valid_candidates = [e for e in extractions if e is not None]
    
    if not valid_candidates:
        return None
        
    # Sort candidates by preference:
    # - confidence 'high' (alphabetically 'high' comes after 'low'? No, 'h' < 'l'. Let's be explicit.)
    # - provider is not null
    # - usage_value is positive
    
    def preference_score(e: ExtractedBillData) -> int:
        score = 0
        if e.confidence.lower() == "high":
            score += 100
        if e.provider:
            score += 10
        if e.usage_value > 0:
            score += 1
        return score
        
    # Sort in descending order of score
    valid_candidates.sort(key=preference_score, reverse=True)
    
    return valid_candidates[0]
