# Database Schema Design

This document outlines the initial Supabase PostgreSQL database schema for the SME Bridge MVP.

## Tables

### 1. `plcs` (Public Listed Companies)
Stores the enterprise clients managing the SMEs.
- `id`: Primary key (UUID).
- `name`: Name of the PLC.
- `created_at` / `updated_at`: Audit timestamps.

### 2. `smes` (Small and Medium Enterprises)
Stores the suppliers mapped to specific PLCs.
- `id`: Primary key (UUID).
- `plc_id`: Foreign key referencing `plcs`.
- `company_name`: The name of the SME supplier.
- `created_at` / `updated_at`: Audit timestamps.

### 3. `authorized_emails`
A whitelist of email addresses permitted to submit utility bills for each SME.
- `id`: Primary key (UUID).
- `sme_id`: Foreign key referencing `smes`.
- `email_address`: A `CITEXT` unique field for case-insensitive exact matching.
- `created_at` / `updated_at`: Audit timestamps.

### 4. `utility_bills`
The core state-machine table tracking every processed bill.
- `status`: Enforced by a CHECK constraint. Valid values are `pending`, `success`, `flagged_low_confidence`, `flagged_unreadable`, `resolved_by_client`.
- `raw_file_url`: Supabase Storage path/URL to the original uploaded file.
- **Extracted Data:** `extracted_provider`, `extracted_period`, `extracted_usage`, `extracted_usage_unit`.
- **Calculated Data:** `calculated_co2e`, `emission_factor_used`.
- **Audit Data:** `reviewer_id` (who performed the HITL approval), `validation_reasons` (why a bill was flagged).
- Indexes are heavily applied on `sme_id`, `status`, and `updated_at` to support dashboard querying.

## How to Apply Migrations in Supabase
Since this is an MVP, you can copy the contents of `apps/api/app/db/migrations/001_initial_schema.sql` and run it directly in the Supabase SQL Editor. 

## Optional Seed Data
To test the pipeline locally, you can insert dummy data after applying the schema:

```sql
INSERT INTO plcs (id, name) 
VALUES ('11111111-1111-1111-1111-111111111111', 'Demo PLC');

INSERT INTO smes (id, plc_id, company_name) 
VALUES ('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'Demo SME Supplier');

INSERT INTO authorized_emails (sme_id, email_address)
VALUES ('22222222-2222-2222-2222-222222222222', 'supplier@example.com');
```
