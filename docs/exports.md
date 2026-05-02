# Export Formats Documentation

The SME Bridge platform supports three primary export formats designed for compliance, audit, and management reporting.

## 1. Bursa Malaysia CSI CSV
**Endpoint:** `GET /exports/csv`

This format is optimized for direct consumption by Bursa Malaysia's Central Sustainability Intelligence (CSI) platform.

| Column | Description |
| --- | --- |
| SME Name | Registered name of the SME supplier. |
| Period | Billing period in YYYY-MM format. |
| Usage | Numeric value of consumption. |
| Usage Unit | Unit of measure (e.g., kWh, m³). |
| CO2e | Calculated carbon footprint in kg CO2e. |
| S3 File Link | Permanent link to the source document image. |

## 2. Raw XLSX Audit Archive
**Endpoint:** `GET /exports/xlsx`

A comprehensive Excel workbook containing the complete audit trail for all processed bills. Useful for internal audits and verification.

**Fields included:**
- `utility_bill_id`: Unique internal ID.
- `status`: Current processing status (success, resolved_by_client).
- `provider`: The identified utility provider (e.g., TNB).
- `emission_factor_used`: The specific factor snapshot used at the time of calculation.
- `reviewer_id`: The ID of the person who manually approved the bill (if applicable).
- `created_at`: Timestamp of bill ingestion.

## 3. Sustainability Summary PDF
**Endpoint:** `GET /exports/pdf`

A management-level report summarizing organizational impact.

**Sections:**
- **Carbon Footprint Summary:** YTD total Scope 3 impact.
- **Category Breakdown:** Comparison of Electricity vs. Water impact.
- **Data Integrity:** Visibility into flagged, unreadable, and successfully processed bills.
