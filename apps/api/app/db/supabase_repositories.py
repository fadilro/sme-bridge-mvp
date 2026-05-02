from typing import Optional, List, Dict, Any, cast
from postgrest.types import CountMethod
from supabase import Client
from app.db.repositories import SmeRepository, UtilityBillRepository
from app.domain.schemas import (
    UtilityBillRecord, 
    ValidatedBillResult,
    DashboardAlertsResponse,
    DashboardOverviewResponse
)
from app.domain.statuses import UtilityBillStatus

class SupabaseSmeRepository(SmeRepository):
    def __init__(self, client: Client):
        self.client = client

    def find_sme_by_authorized_email(self, email: str) -> Optional[Dict[str, Any]]:
        # Supabase allows selecting related table data via PostgREST.
        # We look up the authorized_emails table matching the exact email (which is CITEXT, so case-insensitive),
        # and pull the related smes record.
        response = self.client.table("authorized_emails") \
            .select("sme_id, smes(id, plc_id, company_name)") \
            .eq("email_address", email.strip()) \
            .execute()
        
        if response.data and isinstance(response.data, list) and len(response.data) > 0:
            row = cast(Dict[str, Any], response.data[0])
            return row.get("smes")
        return None

    def find_sme_by_id(self, sme_id: str) -> Optional[Dict[str, Any]]:
        response = self.client.table("smes") \
            .select("id, plc_id, company_name") \
            .eq("id", sme_id) \
            .execute()
            
        if response.data and isinstance(response.data, list) and len(response.data) > 0:
            return cast(Dict[str, Any], response.data[0])
        return None

class SupabaseUtilityBillRepository(UtilityBillRepository):
    def __init__(self, client: Client):
        self.client = client

    def _map_row_to_record(self, row: Dict[str, Any]) -> UtilityBillRecord:
        # Provide default empty list if validation_reasons is None or missing
        validation_reasons = row.get("validation_reasons") or []
        
        return UtilityBillRecord(
            id=row["id"],
            sme_id=row["sme_id"],
            status=UtilityBillStatus(row["status"]),
            raw_file_url=row["raw_file_url"],
            original_filename=row.get("original_filename"),
            extracted_provider=row.get("extracted_provider"),
            extracted_period=row.get("extracted_period"),
            extracted_usage=row.get("extracted_usage"),
            extracted_usage_unit=row.get("extracted_usage_unit"),
            calculated_co2e=row.get("calculated_co2e"),
            emission_factor_used=row.get("emission_factor_used"),
            reviewer_id=row.get("reviewer_id"),
            validation_reasons=validation_reasons,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at")
        )

    def create_pending_utility_bill(self, sme_id: str, raw_file_url: str, original_filename: Optional[str]) -> str:
        payload = {
            "sme_id": sme_id,
            "status": UtilityBillStatus.pending.value,
            "raw_file_url": raw_file_url,
            "original_filename": original_filename
        }
        response = self.client.table("utility_bills").insert(payload).execute()
        if response.data and isinstance(response.data, list) and len(response.data) > 0:
            return str(cast(Dict[str, Any], response.data[0])["id"])
        return ""

    def get_bill(self, bill_id: str) -> Optional[UtilityBillRecord]:
        response = self.client.table("utility_bills").select("*").eq("id", bill_id).execute()
        if response.data and isinstance(response.data, list) and len(response.data) > 0:
            row = cast(Dict[str, Any], response.data[0])
            return self._map_row_to_record(row)
        return None

    def list_bills_by_status(self, status: UtilityBillStatus, limit: int) -> List[UtilityBillRecord]:
        response = self.client.table("utility_bills").select("*").eq("status", status.value).limit(limit).execute()
        if not response.data or not isinstance(response.data, list):
            return []
        return [self._map_row_to_record(cast(Dict[str, Any], row)) for row in response.data]

    def claim_next_pending_bill(self) -> Optional[UtilityBillRecord]:
        # MVP single-worker pseudo-lock: We just pull the oldest pending one.
        # True atomic queue requires an RPC call to a pgplsql function with FOR UPDATE SKIP LOCKED.
        response = self.client.table("utility_bills") \
            .select("*") \
            .eq("status", UtilityBillStatus.pending.value) \
            .order("created_at") \
            .limit(1) \
            .execute()
            
        if response.data and isinstance(response.data, list) and len(response.data) > 0:
            row = cast(Dict[str, Any], response.data[0])
            return self._map_row_to_record(row)
        return None

    def update_bill_extraction_result(self, bill_id: str, result: ValidatedBillResult) -> None:
        payload = {
            "status": result.status.value,
            "calculated_co2e": result.calculated_co2e,
            "emission_factor_used": result.emission_factor_used,
            "validation_reasons": result.validation_reasons,
            "extracted_provider": result.extracted_provider,
            "extracted_period": result.extracted_period,
            "extracted_usage": result.extracted_usage,
            "extracted_usage_unit": result.extracted_unit
        }
        self.client.table("utility_bills").update(payload).eq("id", bill_id).execute()

    def mark_bill_unreadable(self, bill_id: str, reason: str) -> None:
        payload = {
            "status": UtilityBillStatus.flagged_unreadable.value,
            "validation_reasons": [reason]
        }
        self.client.table("utility_bills").update(payload).eq("id", bill_id).execute()

    def approve_bill(self, bill_id: str, reviewer_id: str, provider: str, period: str, usage: float, unit: str, co2e: float) -> None:
        payload = {
            "status": UtilityBillStatus.resolved_by_client.value,
            "reviewer_id": reviewer_id,
            "extracted_provider": provider,
            "extracted_period": period,
            "extracted_usage": usage,
            "extracted_usage_unit": unit,
            "calculated_co2e": co2e
        }
        self.client.table("utility_bills").update(payload).eq("id", bill_id).execute()  # type: ignore

    def get_dashboard_alerts(self, sme_id: str) -> DashboardAlertsResponse:
        low_conf = self.client.table("utility_bills") \
            .select("id", count=CountMethod.exact) \
            .eq("sme_id", sme_id) \
            .eq("status", UtilityBillStatus.flagged_low_confidence.value) \
            .execute()
        unreadable = self.client.table("utility_bills") \
            .select("id", count=CountMethod.exact) \
            .eq("sme_id", sme_id) \
            .eq("status", UtilityBillStatus.flagged_unreadable.value) \
            .execute()
        
        lc_count = low_conf.count if low_conf.count is not None else 0
        un_count = unreadable.count if unreadable.count is not None else 0
        
        return DashboardAlertsResponse(
            flagged_low_confidence_count=lc_count,
            flagged_unreadable_count=un_count,
            total_requiring_review=lc_count + un_count
        )

    def get_dashboard_overview(self, sme_id: str) -> DashboardOverviewResponse:
        # In production, an RPC function should aggregate this on the database side.
        response = self.client.table("utility_bills") \
            .select("calculated_co2e, extracted_usage_unit") \
            .eq("sme_id", sme_id) \
            .in_("status", [UtilityBillStatus.success.value, UtilityBillStatus.resolved_by_client.value]) \
            .execute()
            
        total_co2e = 0.0
        electricity_co2e = 0.0
        water_co2e = 0.0
        
        if response.data and isinstance(response.data, list):
            for row in response.data:
                r = cast(Dict[str, Any], row)
                val = float(r.get("calculated_co2e") or 0.0)
                total_co2e += val
                
                unit = str(r.get("extracted_usage_unit") or "").lower()
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
        query = self.client.table("utility_bills") \
            .select("*") \
            .in_("status", [UtilityBillStatus.success.value, UtilityBillStatus.resolved_by_client.value])
            
        if sme_id:
            query = query.eq("sme_id", sme_id)
            
        response = query.execute()
        if not response.data or not isinstance(response.data, list):
            return []
        return [self._map_row_to_record(cast(Dict[str, Any], row)) for row in response.data]

    def list_bills_by_sme(self, sme_id: Optional[str]) -> List[UtilityBillRecord]:
        query = self.client.table("utility_bills").select("*")
        if sme_id:
            query = query.eq("sme_id", sme_id)
        response = query.execute()
        if not response.data or not isinstance(response.data, list):
            return []
        return [self._map_row_to_record(cast(Dict[str, Any], row)) for row in response.data]
