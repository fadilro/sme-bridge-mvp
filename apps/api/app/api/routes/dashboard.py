from fastapi import APIRouter, Depends
from app.db.repositories import UtilityBillRepository
from app.core.dependencies import get_utility_bill_repository
from app.domain.schemas import DashboardAlertsResponse, DashboardOverviewResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/alerts", response_model=DashboardAlertsResponse)
def get_dashboard_alerts(
    sme_id: str = "test_sme",
    repo: UtilityBillRepository = Depends(get_utility_bill_repository)
) -> DashboardAlertsResponse:
    """
    Returns counts of bills requiring attention (low confidence or unreadable).
    """
    return repo.get_dashboard_alerts(sme_id)

@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    sme_id: str = "test_sme",
    repo: UtilityBillRepository = Depends(get_utility_bill_repository)
) -> DashboardOverviewResponse:
    """
    Returns aggregated CO2e metrics and category breakdown.
    """
    return repo.get_dashboard_overview(sme_id)
