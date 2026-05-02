from app.domain.co2e import calculate_co2e
from app.domain.validation import validate_extracted_bill
from app.domain.schemas import ExtractedBillData
from app.domain.statuses import UtilityBillStatus
from app.domain.emission_factors import get_electricity_emission_factor
from app.core.config import settings

def test_get_electricity_emission_factor() -> None:
    factor = get_electricity_emission_factor()
    assert factor == settings.EMISSION_FACTOR_ELECTRICITY_KWH

def test_calculate_co2e_rounding() -> None:
    # 450.5 * 0.58 = 261.29
    assert calculate_co2e(450.5, 0.58) == 261.29
    
    # 10 * 0.333 = 3.33
    assert calculate_co2e(10, 0.333) == 3.33

def test_validate_none_extraction() -> None:
    result = validate_extracted_bill(None, 0.58)
    assert result.status == UtilityBillStatus.flagged_unreadable
    assert "Extraction failed" in result.validation_reasons[0]

def test_validate_success() -> None:
    extracted = ExtractedBillData(
        provider="TNB",
        billing_period="2026-01",
        usage_value=100.0,
        usage_unit="kWh",
        confidence="high"
    )
    result = validate_extracted_bill(extracted, 0.58)
    assert result.status == UtilityBillStatus.success
    assert result.calculated_co2e == 58.0
    assert result.emission_factor_used == 0.58
    assert len(result.validation_reasons) == 0

def test_validate_low_confidence() -> None:
    extracted = ExtractedBillData(
        provider="TNB",
        billing_period="2026-01",
        usage_value=100.0,
        usage_unit="kWh",
        confidence="low"
    )
    result = validate_extracted_bill(extracted, 0.58)
    assert result.status == UtilityBillStatus.flagged_low_confidence
    assert "Generative confidence is low" in result.validation_reasons

def test_validate_negative_usage() -> None:
    extracted = ExtractedBillData(
        provider="TNB",
        billing_period="2026-01",
        usage_value=-50.0,
        usage_unit="kWh",
        confidence="high"
    )
    result = validate_extracted_bill(extracted, 0.58)
    assert result.status == UtilityBillStatus.flagged_low_confidence
    assert "Usage value must be greater than zero" in result.validation_reasons

def test_validate_unknown_provider() -> None:
    extracted = ExtractedBillData(
        provider="Unknown",
        billing_period="2026-01",
        usage_value=100.0,
        usage_unit="kWh",
        confidence="high"
    )
    result = validate_extracted_bill(extracted, 0.58)
    assert result.status == UtilityBillStatus.flagged_low_confidence
    assert "Provider 'Unknown' is not in the master list" in result.validation_reasons

def test_validate_invalid_unit() -> None:
    extracted = ExtractedBillData(
        provider="TNB",
        billing_period="2026-01",
        usage_value=100.0,
        usage_unit="Liters",
        confidence="high"
    )
    result = validate_extracted_bill(extracted, 0.58)
    assert result.status == UtilityBillStatus.flagged_low_confidence
    assert "Usage unit 'Liters' is not acceptable" in result.validation_reasons[0]
