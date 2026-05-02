import pytest
from pydantic import ValidationError
from app.domain.statuses import UtilityBillStatus
from app.domain.providers import (
    normalize_provider_name,
    is_known_provider
)
from app.domain.schemas import ExtractedBillData

def test_utility_bill_status_enum() -> None:
    assert UtilityBillStatus.pending.value == "pending"
    assert UtilityBillStatus.success.value == "success"
    assert UtilityBillStatus.flagged_low_confidence.value == "flagged_low_confidence"
    assert UtilityBillStatus.flagged_unreadable.value == "flagged_unreadable"
    assert UtilityBillStatus.resolved_by_client.value == "resolved_by_client"

def test_normalize_provider_name() -> None:
    assert normalize_provider_name("  TNB  ") == "tnb"
    assert normalize_provider_name("Air Selangor") == "air selangor"
    assert normalize_provider_name("AIR SELANGOR") == "air selangor"

def test_is_known_provider() -> None:
    # Test valid providers
    assert is_known_provider("TNB") is True
    assert is_known_provider("tnb") is True
    assert is_known_provider("  Air Selangor  ") is True
    
    # Test invalid providers
    assert is_known_provider("Unknown Provider") is False
    assert is_known_provider("") is False

def test_extracted_bill_data_valid() -> None:
    data = ExtractedBillData(
        provider="TNB",
        billing_period="2026-01",
        usage_value=450.5,
        usage_unit="kWh",
        confidence="high"
    )
    assert data.provider == "TNB"
    assert data.billing_period == "2026-01"
    assert data.usage_value == 450.5
    assert data.usage_unit == "kWh"
    assert data.confidence == "high"

def test_extracted_bill_data_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        ExtractedBillData(
            provider="TNB",
            billing_period="2026-01",
            usage_value=450,
            usage_unit="kWh",
            confidence="medium"  # type: ignore
        )

def test_extracted_bill_data_invalid_billing_period() -> None:
    with pytest.raises(ValidationError, match="YYYY-MM format"):
        ExtractedBillData(
            provider="TNB",
            billing_period="January 2026",
            usage_value=450,
            usage_unit="kWh",
            confidence="high"
        )
