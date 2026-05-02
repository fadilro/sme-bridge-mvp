import io
from typing import List, Dict, Optional
from openpyxl import Workbook
from app.domain.schemas import UtilityBillRecord

def generate_raw_xlsx_export(bills: List[UtilityBillRecord], sme_map: Optional[Dict[str, str]] = None) -> bytes:
    """
    Generates a Raw XLSX Audit Archive.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Utility Bills Audit Archive"
    
    # Headers
    headers = [
        "utility_bill_id",
        "plc_id",
        "sme_id",
        "sme_name",
        "status",
        "provider",
        "period",
        "usage",
        "unit",
        "co2e",
        "emission_factor_used",
        "raw_file_url",
        "reviewer_id",
        "created_at",
        "updated_at"
    ]
    ws.append(headers)
    
    # Data
    for bill in bills:
        sme_name = sme_map.get(bill.sme_id, "SME " + bill.sme_id) if sme_map else "SME " + bill.sme_id
        
        row = [
            bill.id,
            "", # plc_id - not directly in UtilityBillRecord for now
            bill.sme_id,
            sme_name,
            bill.status.value,
            bill.extracted_provider or "",
            bill.extracted_period or "",
            bill.extracted_usage or 0.0,
            bill.extracted_usage_unit or "",
            bill.calculated_co2e or 0.0,
            bill.emission_factor_used or 0.0,
            bill.raw_file_url,
            bill.reviewer_id or "",
            bill.created_at or "",
            bill.updated_at or ""
        ]
        ws.append(row)
    
    # Save to buffer
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
