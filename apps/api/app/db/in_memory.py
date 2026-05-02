import uuid
from typing import Optional, List, Dict, Any
from app.db.repositories import SmeRepository, UtilityBillRepository
from app.domain.schemas import (
    UtilityBillRecord, 
    ValidatedBillResult,
    DashboardAlertsResponse,
    DashboardOverviewResponse
)
from app.domain.statuses import UtilityBillStatus

class InMemorySmeRepository(SmeRepository):
    def __init__(self) -> None:
        self.plcs: Dict[str, Dict[str, Any]] = {}
        self.smes: Dict[str, Dict[str, Any]] = {}
        self.authorized_emails: Dict[str, str] = {}  # email (lowercase) -> sme_id

    def add_plc(self, plc_id: str, name: str) -> None:
        self.plcs[plc_id] = {"id": plc_id, "name": name}

    def add_sme(self, sme_id: str, plc_id: str, company_name: str) -> None:
        self.smes[sme_id] = {"id": sme_id, "plc_id": plc_id, "company_name": company_name}

    def authorize_email(self, sme_id: str, email: str) -> None:
        self.authorized_emails[email.strip().lower()] = sme_id

    def find_sme_by_id(self, sme_id: str) -> Optional[Dict[str, Any]]:
        return self.smes.get(sme_id)

    def find_sme_by_authorized_email(self, email: str) -> Optional[Dict[str, Any]]:
        sme_id = self.authorized_emails.get(email.strip().lower())
        if sme_id:
            return self.smes.get(sme_id)
        return None

class InMemoryUtilityBillRepository(UtilityBillRepository):
    def __init__(self) -> None:
        self.bills: Dict[str, UtilityBillRecord] = {}
        self._claimed_bills: set[str] = set()

    def create_pending_utility_bill(self, sme_id: str, raw_file_url: str, original_filename: Optional[str]) -> str:
        bill_id = str(uuid.uuid4())
        bill = UtilityBillRecord(
            id=bill_id,
            sme_id=sme_id,
            status=UtilityBillStatus.pending,
            raw_file_url=raw_file_url,
            original_filename=original_filename,
            validation_reasons=[],
            created_at="2024-05-01T12:00:00Z", # Mock
            updated_at="2024-05-01T12:00:00Z"
        )
        self.bills[bill_id] = bill
        return bill_id

    def get_bill(self, bill_id: str) -> Optional[UtilityBillRecord]:
        return self.bills.get(bill_id)

    def list_bills_by_status(self, status: UtilityBillStatus, limit: int) -> List[UtilityBillRecord]:
        results = [b for b in self.bills.values() if b.status == status]
        return results[:limit]

    def claim_next_pending_bill(self) -> Optional[UtilityBillRecord]:
        for bill in self.bills.values():
            if bill.status == UtilityBillStatus.pending and bill.id not in self._claimed_bills:
                self._claimed_bills.add(bill.id)
                return bill
        return None

    def update_bill_extraction_result(self, bill_id: str, result: ValidatedBillResult) -> None:
        if bill_id in self.bills:
            bill = self.bills[bill_id]
            bill.status = result.status
            bill.calculated_co2e = result.calculated_co2e
            bill.emission_factor_used = result.emission_factor_used
            bill.validation_reasons = result.validation_reasons
            bill.extracted_provider = result.extracted_provider
            bill.extracted_period = result.extracted_period
            bill.extracted_usage = result.extracted_usage
            bill.extracted_usage_unit = result.extracted_unit
            
            # Since we updated the state, it's no longer pending, so remove from claimed set
            # (In a real DB, the status change acts as the release of the lock)
            if bill_id in self._claimed_bills:
                self._claimed_bills.remove(bill_id)

    def mark_bill_unreadable(self, bill_id: str, reason: str) -> None:
        if bill_id in self.bills:
            bill = self.bills[bill_id]
            bill.status = UtilityBillStatus.flagged_unreadable
            bill.validation_reasons = [reason]
            if bill_id in self._claimed_bills:
                self._claimed_bills.remove(bill_id)

    def approve_bill(self, bill_id: str, reviewer_id: str, provider: str, period: str, usage: float, unit: str, co2e: float) -> None:
        if bill_id in self.bills:
            bill = self.bills[bill_id]
            bill.status = UtilityBillStatus.resolved_by_client
            bill.reviewer_id = reviewer_id
            bill.extracted_provider = provider
            bill.extracted_period = period
            bill.extracted_usage = usage
            bill.extracted_usage_unit = unit
            bill.calculated_co2e = co2e

    def get_alert_counts(self) -> Dict[str, int]:
        counts = {"low_confidence": 0, "unreadable": 0}
        for bill in self.bills.values():
            if bill.status == UtilityBillStatus.flagged_low_confidence:
                counts["low_confidence"] += 1
            elif bill.status == UtilityBillStatus.flagged_unreadable:
                counts["unreadable"] += 1
        return counts

    def get_dashboard_alerts(self, sme_id: str) -> DashboardAlertsResponse:
        low_confidence = 0
        unreadable = 0
        for bill in self.bills.values():
            if bill.sme_id == sme_id:
                if bill.status == UtilityBillStatus.flagged_low_confidence:
                    low_confidence += 1
                elif bill.status == UtilityBillStatus.flagged_unreadable:
                    unreadable += 1
        
        return DashboardAlertsResponse(
            flagged_low_confidence_count=low_confidence,
            flagged_unreadable_count=unreadable,
            total_requiring_review=low_confidence + unreadable
        )

    def get_dashboard_overview(self, sme_id: str) -> DashboardOverviewResponse:
        total_co2e = 0.0
        electricity_co2e = 0.0
        water_co2e = 0.0
        
        for bill in self.bills.values():
            if bill.sme_id == sme_id:
                if bill.status in (UtilityBillStatus.success, UtilityBillStatus.resolved_by_client):
                    val = bill.calculated_co2e or 0.0
                    total_co2e += val
                    
                    # Logic: kWh -> electricity, m3 -> water
                    unit = (bill.extracted_usage_unit or "").lower()
                    if "kwh" in unit:
                        electricity_co2e += val
                    elif "m3" in unit:
                        water_co2e += val
                    
        return DashboardOverviewResponse(
            total_co2e_ytd=round(total_co2e, 2),
            electricity_co2e=round(electricity_co2e, 2),
            water_co2e=round(water_co2e, 2)
        )

    def list_bills_for_export(self, sme_id: Optional[str] = None) -> List[UtilityBillRecord]:
        return [
            b for b in self.bills.values()
            if b.status in (UtilityBillStatus.success, UtilityBillStatus.resolved_by_client)
            and (sme_id is None or b.sme_id == sme_id)
        ]

    def list_bills_by_sme(self, sme_id: Optional[str]) -> List[UtilityBillRecord]:
        return [
            b for b in self.bills.values()
            if sme_id is None or b.sme_id == sme_id
        ]
