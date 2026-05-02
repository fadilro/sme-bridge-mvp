import re
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator
from app.domain.statuses import UtilityBillStatus

class ExtractedBillData(BaseModel):
    provider: str
    billing_period: str
    usage_value: float
    usage_unit: str
    confidence: Literal["high", "low"]

    @field_validator('billing_period')
    def validate_billing_period(cls, v: str) -> str:
        # Regex matching YYYY-MM
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("billing_period must be in YYYY-MM format")
        return v

class ValidatedBillResult(BaseModel):
    status: UtilityBillStatus
    calculated_co2e: Optional[float] = None
    emission_factor_used: Optional[float] = None
    validation_reasons: List[str] = Field(default_factory=list)
    extracted_provider: Optional[str] = None
    extracted_period: Optional[str] = None
    extracted_usage: Optional[float] = None
    extracted_unit: Optional[str] = None

class UtilityBillRecord(BaseModel):
    id: str
    sme_id: str
    status: UtilityBillStatus
    raw_file_url: str
    original_filename: Optional[str] = None
    extracted_provider: Optional[str] = None
    extracted_period: Optional[str] = None
    extracted_usage: Optional[float] = None
    extracted_usage_unit: Optional[str] = None
    calculated_co2e: Optional[float] = None
    emission_factor_used: Optional[float] = None
    reviewer_id: Optional[str] = None
    validation_reasons: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class AttachmentMetadata(BaseModel):
    filename: str
    content_type: str
    size_bytes: int

class DashboardAlertsResponse(BaseModel):
    flagged_low_confidence_count: int
    flagged_unreadable_count: int
    total_requiring_review: int

class DashboardOverviewResponse(BaseModel):
    total_co2e_ytd: float
    electricity_co2e: float
    water_co2e: float

class BillApprovalRequest(BaseModel):
    provider: str
    billing_period: str
    usage_value: float
    usage_unit: str
