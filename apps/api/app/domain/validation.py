from typing import Optional
from app.domain.schemas import ExtractedBillData, ValidatedBillResult
from app.domain.statuses import UtilityBillStatus
from app.domain.providers import is_known_provider
from app.domain.co2e import calculate_co2e

def validate_extracted_bill(
    extracted: Optional[ExtractedBillData],
    emission_factor: float
) -> ValidatedBillResult:
    """
    Implements the Two-Key Validation state machine.
    """
    if not extracted:
        return ValidatedBillResult(
            status=UtilityBillStatus.flagged_unreadable,
            validation_reasons=["Extraction failed or missing payload"]
        )

    reasons = []
    
    # Key 1: Generative Key
    generative_key_pass = extracted.confidence == "high"
    if not generative_key_pass:
        reasons.append("Generative confidence is low")

    # Key 2: Deterministic Key
    deterministic_key_pass = True
    
    if extracted.usage_value <= 0:
        deterministic_key_pass = False
        reasons.append("Usage value must be greater than zero")
        
    if not is_known_provider(extracted.provider):
        deterministic_key_pass = False
        reasons.append(f"Provider '{extracted.provider}' is not in the master list")
        
    # We enforce 'kwh' (case-insensitive) for electricity for MVP
    if extracted.usage_unit.lower() != "kwh":
        deterministic_key_pass = False
        reasons.append(f"Usage unit '{extracted.usage_unit}' is not acceptable (expected 'kWh')")

    if generative_key_pass and deterministic_key_pass:
        co2e = calculate_co2e(extracted.usage_value, emission_factor)
        return ValidatedBillResult(
            status=UtilityBillStatus.success,
            calculated_co2e=co2e,
            emission_factor_used=emission_factor
        )

    return ValidatedBillResult(
        status=UtilityBillStatus.flagged_low_confidence,
        validation_reasons=reasons
    )
