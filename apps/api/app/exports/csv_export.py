import csv
import io
from typing import List, Dict, Optional
from app.domain.schemas import UtilityBillRecord

def generate_csi_csv_export(bills: List[UtilityBillRecord], sme_map: Optional[Dict[str, str]] = None) -> str:
    """
    Generates a CSV string in the Bursa Malaysia CSI format.
    Columns: SME Name, Period, Usage, Usage Unit, CO2e, S3 File Link
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write Header
    writer.writerow([
        "SME Name",
        "Period",
        "Usage",
        "Usage Unit",
        "CO2e",
        "S3 File Link"
    ])
    
    # Write Rows
    for bill in bills:
        sme_name = sme_map.get(bill.sme_id, "SME " + bill.sme_id) if sme_map else "SME " + bill.sme_id
        
        writer.writerow([
            sme_name,
            bill.extracted_period or "",
            bill.extracted_usage or 0.0,
            bill.extracted_usage_unit or "",
            bill.calculated_co2e or 0.0,
            bill.raw_file_url
        ])
    
    return output.getvalue()
