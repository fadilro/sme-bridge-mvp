from typing import Optional, Dict
from fastapi import APIRouter, Depends, Query, Response

from app.db.repositories import UtilityBillRepository, SmeRepository
from app.core.dependencies import get_utility_bill_repository, get_sme_repository
from app.exports.csv_export import generate_csi_csv_export
from app.exports.xlsx_export import generate_raw_xlsx_export
from app.exports.pdf_generator import generate_sustainability_summary_pdf

router = APIRouter(prefix="/exports", tags=["Exports"])

def get_sme_map(sme_id: Optional[str], sme_repo: SmeRepository) -> Dict[str, str]:
    """Helper to get a map of SME IDs to Company Names"""
    sme_map = {}
    if sme_id:
        sme = sme_repo.find_sme_by_id(sme_id)
        if sme:
            sme_map[sme_id] = sme.get("company_name", f"SME {sme_id}")
    return sme_map

@router.get("/csv")
def export_bills_csv(
    sme_id: Optional[str] = Query(None, description="Filter by SME ID"),
    repo: UtilityBillRepository = Depends(get_utility_bill_repository),
    sme_repo: SmeRepository = Depends(get_sme_repository)
) -> Response:
    """
    Exports processed and resolved utility bills to CSI-compliant CSV.
    """
    bills = repo.list_bills_for_export(sme_id=sme_id)
    sme_map = get_sme_map(sme_id, sme_repo)
    csv_content = generate_csi_csv_export(bills, sme_map)
    
    filename = f"csi_export_{sme_id or 'all'}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/xlsx")
def export_bills_xlsx(
    sme_id: Optional[str] = Query(None, description="Filter by SME ID"),
    repo: UtilityBillRepository = Depends(get_utility_bill_repository),
    sme_repo: SmeRepository = Depends(get_sme_repository)
) -> Response:
    """
    Exports processed and resolved utility bills to Raw XLSX Audit Archive.
    """
    bills = repo.list_bills_for_export(sme_id=sme_id)
    sme_map = get_sme_map(sme_id, sme_repo)
    xlsx_bytes = generate_raw_xlsx_export(bills, sme_map)
    
    filename = f"audit_archive_{sme_id or 'all'}.xlsx"
    
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/pdf")
def export_sustainability_summary(
    sme_id: str = Query(..., description="SME ID for the report"),
    bill_repo: UtilityBillRepository = Depends(get_utility_bill_repository),
    sme_repo: SmeRepository = Depends(get_sme_repository)
) -> Response:
    """
    Generates a PDF sustainability summary for an SME.
    """
    # 1. Gather data
    sme = sme_repo.find_sme_by_id(sme_id) if hasattr(sme_repo, "find_sme_by_id") else None
    # For MVP in-memory, we might need a better way. 
    # Let's assume we can get it or use a default.
    sme_name = "Organization"
    if sme:
        sme_name = sme.get("company_name", "Organization")
        
    overview = bill_repo.get_dashboard_overview(sme_id)
    alerts = bill_repo.get_dashboard_alerts(sme_id)
    
    # 2. Generate PDF
    pdf_bytes = generate_sustainability_summary_pdf(sme_name, overview, alerts)
    
    filename = f"sustainability_summary_{sme_id}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
