from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.repositories import UtilityBillRepository
from app.core.dependencies import get_utility_bill_repository, get_current_user_id
from app.core.config import get_settings, Settings
from app.domain.schemas import UtilityBillRecord, BillApprovalRequest

router = APIRouter(prefix="/bills", tags=["bills"])

@router.get("", response_model=List[UtilityBillRecord])
def list_bills(
    sme_id: Optional[str] = Query(None),
    repo: UtilityBillRepository = Depends(get_utility_bill_repository)
) -> List[UtilityBillRecord]:
    """
    Lists all bills, optionally filtered by SME.
    """
    # We can reuse list_bills_for_export or implement a more general list method.
    # For now, let's use list_bills_for_export but it filters by status.
    # We need a method that lists ALL bills for the review page.
    return repo.list_bills_by_sme(sme_id) if hasattr(repo, "list_bills_by_sme") else []

@router.get("/{bill_id}", response_model=UtilityBillRecord)
def get_bill_detail(
    bill_id: str,
    repo: UtilityBillRepository = Depends(get_utility_bill_repository)
) -> UtilityBillRecord:
    """
    Returns full details of a specific bill.
    """
    bill = repo.get_bill(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

@router.post("/{bill_id}/approve", response_model=None)
def approve_bill(
    bill_id: str,
    request: BillApprovalRequest,
    repo: UtilityBillRepository = Depends(get_utility_bill_repository),
    reviewer_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Manually approves a bill with reviewed data.
    Recalculates CO2e server-side based on emission factors.
    """
    bill = repo.get_bill(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    # Simple recalculation logic
    co2e = 0.0
    if "kwh" in request.usage_unit.lower():
        co2e = request.usage_value * settings.EMISSION_FACTOR_ELECTRICITY_KWH
    else:
        # Placeholder for other factors
        co2e = 0.0
        
    repo.approve_bill(
        bill_id, 
        reviewer_id,
        request.provider,
        request.billing_period,
        request.usage_value,
        request.usage_unit,
        round(co2e, 4)
    )
    return {"status": "success", "bill_id": bill_id}
