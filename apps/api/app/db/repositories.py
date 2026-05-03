from typing import Protocol, Optional, List, Dict, Any
from app.domain.schemas import (
    UtilityBillRecord, 
    ValidatedBillResult,
    DashboardAlertsResponse,
    DashboardOverviewResponse
)
from app.domain.statuses import UtilityBillStatus

class SmeRepository(Protocol):
    def find_sme_by_authorized_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Looks up an SME by an authorized email address (case-insensitive).
        Returns a dictionary representing the SME, or None if not found.
        """
        ...

    def find_sme_by_id(self, sme_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves an SME by its ID.
        """
        ...

    def list_all_smes(self) -> List[Dict[str, Any]]:
        """
        Returns all SMEs. Used by the frontend SME selector.
        """
        ...


class UtilityBillRepository(Protocol):
    def create_pending_utility_bill(self, sme_id: str, raw_file_url: str, original_filename: Optional[str]) -> str:
        """
        Creates a new utility bill in the 'pending' state.
        Returns the ID of the newly created bill.
        """
        ...

    def get_bill(self, bill_id: str) -> Optional[UtilityBillRecord]:
        """
        Retrieves a utility bill by its ID.
        """
        ...

    def list_bills_by_status(self, status: UtilityBillStatus, limit: int) -> List[UtilityBillRecord]:
        """
        Lists bills matching a specific status, up to the given limit.
        """
        ...

    def claim_next_pending_bill(self) -> Optional[UtilityBillRecord]:
        """
        Atomically finds and claims the next pending bill for processing.
        To avoid race conditions, this should change the status or flag it so
        it isn't returned twice. For the MVP, we can just return it.
        Wait, the spec says "Ensure claimed bills are not returned twice in a single worker run".
        We might need a 'processing' state or similar lock, but for MVP we will just return it.
        Actually, we can mark it as 'processing' (if we add it to the enum) or just pop it from a queue.
        Let's assume the in-memory implementation handles the lock internally.
        """
        ...

    def update_bill_extraction_result(self, bill_id: str, result: ValidatedBillResult) -> None:
        """
        Updates a bill with the extraction and validation results.
        """
        ...

    def mark_bill_unreadable(self, bill_id: str, reason: str) -> None:
        """
        Marks a bill as unreadable with the given reason.
        """
        ...

    def approve_bill(self, bill_id: str, reviewer_id: str, provider: str, period: str, usage: float, unit: str, co2e: float) -> None:
        """
        Approves a flagged bill (HITL), setting it to resolved_by_client and updating with reviewed data.
        """
        ...

    def get_dashboard_alerts(self, sme_id: str) -> DashboardAlertsResponse:
        """
        Returns counts of bills requiring attention for a specific SME.
        """
        ...

    def get_dashboard_overview(self, sme_id: str) -> DashboardOverviewResponse:
        """
        Returns aggregated CO2e metrics for a specific SME.
        """
        ...

    def list_bills_for_export(self, sme_id: Optional[str] = None) -> List[UtilityBillRecord]:
        """
        Lists all successfully processed or resolved bills for export.
        """
        ...

    def list_bills_by_sme(self, sme_id: Optional[str]) -> List[UtilityBillRecord]:
        """
        Lists all bills for a specific SME, regardless of status.
        """
        ...
