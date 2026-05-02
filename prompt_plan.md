Based on the uploaded SME Bridge MVP technical specification, the project is a FastAPI + Supabase + local Gemma/Ollama pipeline for receiving SME utility bills by email, extracting audit-ready Scope 3 data, validating it, supporting human review, and exporting Bursa Malaysia CSI-ready outputs. 

I’ll assume the frontend stack is **React + TypeScript + Vite**, since the spec defines dashboard behavior but not a frontend framework. Everything else follows the provided spec: **FastAPI**, **Supabase PostgreSQL + Storage**, **local Gemma via Ollama/HuggingFace**, sequential GPU-safe processing, HITL review, and CSV/XLSX/PDF export.

---

# 1. Detailed Step-by-Step Blueprint

## 1.1 Core Product Flow

The MVP has one main lifecycle:

1. SME supplier emails one or more utility bills to `submit@smebridge.com`.
2. Email provider sends a webhook payload to FastAPI.
3. FastAPI checks whether the sender is authorized.
4. If unauthorized, the system drops the payload and sends a bounce-style response email.
5. If authorized, each attachment is saved to Supabase Storage.
6. A `utility_bills` row is created with status `pending`.
7. A background worker picks up pending bills one at a time.
8. PDFs are converted to page images.
9. Images are resized, grayscaled, thresholded, and processed sequentially.
10. Each page is sent to the local Gemma model.
11. Gemma returns strict JSON.
12. Python validates the JSON using the two-key validation logic.
13. If validation passes, CO2e is calculated and the bill becomes `success`.
14. If confidence or deterministic validation fails, the bill becomes `flagged_low_confidence`.
15. If extraction breaks, the file is unreadable, or the PDF is corrupted/password-protected, the bill becomes `flagged_unreadable`.
16. PLC admin dashboard shows alerts, metrics, flagged bills, and the HITL verification UI.
17. Admin reviews flagged bills side by side with the source image.
18. Admin edits extracted values, sees live CO2e recalculation, and approves.
19. Approved reviewed bills are marked `resolved_by_client` and stamped with `reviewer_id`.
20. Admin exports CSI CSV, raw XLSX audit archive, or PDF sustainability summary.

---

## 1.2 Major System Components

### Backend API

Use **FastAPI** with a layered architecture:

```text
apps/api/
  app/
    main.py
    core/
      config.py
      logging.py
      errors.py
    domain/
      statuses.py
      providers.py
      emission_factors.py
      schemas.py
      validation.py
      co2e.py
    db/
      repositories.py
      supabase_client.py
      migrations/
    storage/
      base.py
      local_storage.py
      supabase_storage.py
    email/
      webhook_parser.py
      authorization.py
      bounce.py
    processing/
      file_loader.py
      pdf_converter.py
      image_preprocessor.py
      llm_prompt.py
      llm_client.py
      extraction_parser.py
      processor.py
      worker.py
    api/
      routes/
        health.py
        email_webhook.py
        dashboard.py
        review.py
        exports.py
    exports/
      csv_export.py
      xlsx_export.py
      pdf_export.py
    tests/
```

### Frontend App

Use **React + TypeScript + Vite**:

```text
apps/web/
  src/
    main.tsx
    App.tsx
    api/
      client.ts
      types.ts
    routes/
      DashboardPage.tsx
      ReviewBillPage.tsx
      ExportsPage.tsx
    components/
      AlertsBar.tsx
      ImpactOverview.tsx
      BreakdownChart.tsx
      BillImageViewer.tsx
      VerificationForm.tsx
      ExportModal.tsx
    tests/
```

### Database

Supabase PostgreSQL tables:

```text
plcs
smes
authorized_emails
utility_bills
```

The `utility_bills` table is the state-machine table. It stores:

```text
pending
success
flagged_low_confidence
flagged_unreadable
resolved_by_client
```

### Storage

Supabase Storage stores raw attachments and processed image artifacts if needed.

Suggested storage structure:

```text
utility-bills/
  raw/
    {sme_id}/{utility_bill_id}/{original_filename}
  processed/
    {sme_id}/{utility_bill_id}/page-1.png
    {sme_id}/{utility_bill_id}/page-2.png
```

### Worker

For MVP simplicity, use a **database-backed worker loop** instead of introducing Celery immediately.

The worker should:

1. Claim one `pending` bill.
2. Process it fully.
3. Update final state.
4. Release resources.
5. Move to the next bill.

This is easier to test than Celery and respects the local RTX 3060 VRAM constraint.

---

## 1.3 Backend Domain Design

### Status Enum

Create a single source of truth for utility bill statuses:

```text
pending
success
flagged_low_confidence
flagged_unreadable
resolved_by_client
```

### Provider Validation

Start with a master list:

```text
TNB
Air Selangor
Sarawak Energy
Sabah Electricity
Indah Water
```

Use aliases later, but begin with deterministic exact or normalized matching.

### Emission Factors

Use hardcoded factors for MVP, with the value copied onto every `utility_bills` row for auditability.

Suggested design:

```text
EmissionFactorSnapshot:
  region: Malaysia
  utility_type: electricity
  unit: kWh
  factor: decimal
  source_label: "Hardcoded MVP Malaysian Grid Emission Factor"
```

The exact factor value should be configured in one place and covered by unit tests.

### Two-Key Validation

Implement this as a pure function first.

Input:

```json
{
  "provider": "TNB",
  "billing_period": "2026-01",
  "usage_value": 450,
  "usage_unit": "kWh",
  "confidence": "high"
}
```

Validation rules:

1. JSON exists and contains required fields.
2. `confidence === "high"` passes the generative key.
3. `usage_value` is a positive number.
4. `provider` is in the Malaysian utility provider master list.
5. `usage_unit` is acceptable for that provider or utility category.

Routing:

```text
broken JSON or missing critical data -> flagged_unreadable
confidence high + deterministic validation pass -> success
otherwise -> flagged_low_confidence
```

---

## 1.4 Email Webhook Design

The webhook route must return quickly.

Endpoint:

```text
POST /webhook/incoming-email
```

Synchronous work only:

1. Parse webhook payload.
2. Extract `From` email.
3. Check authorization.
4. If unauthorized, trigger bounce service and return `200`.
5. For each attachment:

   * Save raw attachment.
   * Create one `utility_bills` row with status `pending`.
6. Return `200`.

Do **not** run LLM extraction inside the webhook route.

This prevents provider retries from creating duplicate processing.

---

## 1.5 Processing Pipeline Design

### File Handling

Support:

```text
PDF
PNG
JPG
JPEG
```

Flow:

1. Download raw file from storage.
2. Detect file type.
3. If PDF:

   * Convert each page to image with `pdf2image`.
   * If conversion fails, mark `flagged_unreadable`.
4. If image:

   * Load image directly.
5. For each page/image:

   * Resize max dimension to 1024 px.
   * Convert to grayscale.
   * Apply adaptive thresholding.
   * Do not auto-crop.
6. Send one page at a time to Gemma.
7. Clear VRAM after each page.
8. Aggregate outputs.

### LLM Abstraction

Create an interface:

```text
LLMClient.extract_bill_data(image_bytes, prompt) -> str
```

Implement:

```text
FakeLLMClient for tests
OllamaGemmaClient for local runtime
```

This prevents tests from needing the real model.

### Prompt Builder

Create one prompt builder function that instructs Gemma to return only JSON:

```json
{
  "provider": "TNB",
  "billing_period": "YYYY-MM",
  "usage_value": 450,
  "usage_unit": "kWh",
  "confidence": "high"
}
```

### OOM Handling

Catch GPU/runtime exceptions around inference.

On error:

1. Log the error.
2. Call `torch.cuda.empty_cache()` when available.
3. Mark the bill `flagged_unreadable`.
4. Continue worker loop.

---

## 1.6 Dashboard API Design

### Alerts

```text
GET /dashboard/alerts
```

Returns counts:

```json
{
  "flagged_low_confidence": 5,
  "flagged_unreadable": 2,
  "total_requiring_review": 7
}
```

### Overview

```text
GET /dashboard/overview
```

Returns:

```json
{
  "total_scope3_co2e_ytd": 12345.67,
  "breakdown": {
    "electricity": 11000.22,
    "water": 1345.45
  }
}
```

### Bill Detail

```text
GET /bills/{bill_id}
```

Returns bill metadata and raw file URL.

### Approve Review

```text
POST /bills/{bill_id}/approve
```

Input:

```json
{
  "provider": "TNB",
  "billing_period": "2026-01",
  "usage_value": 500,
  "usage_unit": "kWh"
}
```

Backend recalculates CO2e and sets:

```text
status = resolved_by_client
reviewer_id = current user id
updated_at = now
```

---

## 1.7 Frontend Design

### Dashboard

Components:

```text
AlertsBar
ImpactOverview
BreakdownChart
FlaggedBillsList
ExportModal
```

### HITL Review Page

Side-by-side layout:

```text
Left pane:
  raw bill image/PDF preview
  zoom controls
  rotate controls

Right pane:
  provider field
  billing period field
  usage value field
  usage unit field
  calculated CO2e read-only field
  approve button
```

Live math:

```text
calculated_co2e = usage_value * emission_factor
```

The backend still performs authoritative recalculation on approval.

---

## 1.8 Export Design

### CSI CSV

Columns:

```text
SME Name
Period
Usage
Usage Unit
CO2e
S3 File Link
```

### Raw XLSX Archive

Include complete audit trail:

```text
utility_bill_id
plc_id
sme_id
sme_name
status
provider
period
usage
unit
co2e
emission_factor_used
raw_file_url
reviewer_id
created_at
updated_at
```

### PDF Summary

High-level management report:

```text
total CO2e
YTD trend
electricity vs water breakdown
review counts
unreadable counts
```

---

# 2. Iterative Breakdown

## 2.1 First-Pass Chunks

At the highest level, the project breaks into these chunks:

1. Repository, tooling, and environment setup.
2. Backend domain logic.
3. Database schema and repository layer.
4. Storage layer.
5. Email webhook ingestion.
6. Processing worker.
7. LLM extraction pipeline.
8. Dashboard APIs.
9. HITL review APIs.
10. Export generation.
11. Frontend dashboard.
12. Frontend HITL review UI.
13. Integration testing.
14. Local deployment setup.

This is still too coarse. For example, “processing worker” includes file loading, PDF conversion, image preprocessing, LLM calls, aggregation, status transitions, and GPU cleanup.

---

## 2.2 Second-Pass Breakdown

Break the coarse chunks into safer delivery units:

1. Monorepo skeleton.
2. Backend health endpoint.
3. Backend config and environment validation.
4. Domain enums and schemas.
5. CO2e calculator.
6. Two-key validation.
7. SQL migrations.
8. Repository interface.
9. In-memory repository for tests.
10. Supabase repository implementation.
11. Storage interface.
12. Local storage implementation.
13. Supabase storage implementation.
14. Webhook payload parser.
15. Authorized email checker.
16. Bounce email abstraction.
17. Incoming email webhook route.
18. Multiple-attachment handling.
19. Worker claim-next-pending-bill flow.
20. File loader.
21. PDF-to-image conversion.
22. Image preprocessing.
23. LLM prompt builder.
24. LLM client abstraction.
25. Fake LLM implementation.
26. Ollama/Gemma implementation.
27. JSON extraction parser.
28. Multi-page aggregation.
29. Processing state machine.
30. OOM handling.
31. Dashboard alert API.
32. Dashboard overview API.
33. Bill detail API.
34. Review approval API.
35. CSV export.
36. XLSX export.
37. PDF export.
38. Frontend API client.
39. Frontend dashboard shell.
40. Alerts bar.
41. Overview cards/chart.
42. Review page route.
43. Bill image viewer.
44. Verification form.
45. Live CO2e math.
46. Approval submission.
47. Export modal.
48. End-to-end tests.
49. Local tunnel/deployment documentation.

This is safer, but a few steps are now too small to justify separate LLM prompts. Some should be combined when they share one testable seam.

---

## 2.3 Final Right-Sized Implementation Sequence

These are the final implementation steps I would use for a code-generation LLM. Each step has a clear test target, integrates with previous work, and avoids orphaned code.

1. Bootstrap monorepo, quality tools, and test runners.
2. Create FastAPI app shell with config and health endpoint.
3. Add backend domain models, status enum, provider list, and schemas.
4. Implement CO2e calculator and two-key validation.
5. Add database migration SQL for Supabase schema.
6. Add repository contracts and in-memory repository.
7. Add Supabase repository implementation.
8. Add storage contracts, local storage, and Supabase storage.
9. Implement email webhook payload parsing.
10. Implement authorized sender checking and bounce abstraction.
11. Implement incoming email webhook route with multiple attachment handling.
12. Add worker skeleton that claims and processes pending bills.
13. Implement file loading and PDF/image normalization.
14. Implement image preprocessing.
15. Implement LLM prompt builder, LLM interface, and fake LLM.
16. Implement Ollama/Gemma client behind the interface.
17. Implement extraction JSON parser and multi-page aggregation.
18. Wire full bill processing state machine.
19. Add OOM/corrupt-file hardening.
20. Add dashboard alerts and overview APIs.
21. Add bill detail and HITL approval APIs.
22. Add CSV and XLSX exports.
23. Add PDF summary export.
24. Create frontend shell and typed API client.
25. Build dashboard alerts and overview UI.
26. Build HITL review UI with live CO2e math.
27. Build export modal.
28. Add end-to-end integration tests and local deployment docs.

---

# 3. Code-Generation LLM Prompts

Use these prompts in order. Each one assumes the previous prompt has already been completed and committed.

---

## Prompt 01 — Bootstrap the Monorepo

```text
You are implementing the SME Bridge MVP.

Goal:
Create the initial monorepo structure, developer tooling, test runners, and quality gates. Do not implement product logic yet.

Required stack:
- Backend: Python 3.11+, FastAPI, pytest
- Frontend: React + TypeScript + Vite
- Package management may use pip/requirements or Poetry for Python, and npm/pnpm for frontend. Choose one and document it.
- Use ruff for Python linting.
- Use mypy or pyright for Python type checking if practical.
- Use Vitest and React Testing Library for frontend tests.

Create this structure:

apps/
  api/
  web/
docs/
scripts/

Backend requirements:
- Create apps/api/app as a Python package.
- Create apps/api/tests.
- Add a minimal pytest test that verifies the test runner works.
- Add backend lint/typecheck scripts.

Frontend requirements:
- Create a Vite React TypeScript app in apps/web.
- Add a minimal component test that verifies the frontend test runner works.
- Add frontend lint/test scripts.

Root requirements:
- Add a README.md explaining how to install, test, lint, and run both apps.
- Add a .gitignore suitable for Python, Node, local env files, build artifacts, and test caches.
- Add a docs/architecture.md stub with the intended components:
  - FastAPI backend
  - Supabase PostgreSQL
  - Supabase Storage
  - local Gemma/Ollama extraction worker
  - React dashboard

Testing instructions:
1. Write the minimal failing tests first.
2. Implement only enough code/configuration to make them pass.
3. Run backend tests.
4. Run frontend tests.
5. Run lint commands where configured.

Done criteria:
- Backend tests pass.
- Frontend tests pass.
- README contains exact local commands.
- No product-specific orphan code has been added yet.
```

---

## Prompt 02 — FastAPI App Shell, Config, and Health Endpoint

```text
You are continuing the SME Bridge MVP from Prompt 01.

Goal:
Create the FastAPI application shell with typed configuration and a health endpoint. This should establish the backend app pattern used by all later prompts.

Implement:
- apps/api/app/main.py with a create_app() factory.
- apps/api/app/core/config.py with a Settings object.
- Environment-driven settings for:
  - APP_ENV
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY
  - SUPABASE_STORAGE_BUCKET
  - OLLAMA_BASE_URL
  - GEMMA_MODEL_NAME
  - EMISSION_FACTOR_ELECTRICITY_KWH
- Sensible test defaults so tests do not require real Supabase or Ollama credentials.
- apps/api/app/api/routes/health.py with:
  GET /health
  returning:
  {
    "status": "ok",
    "service": "sme-bridge-api"
  }

Wire:
- Register the health route in create_app().
- Ensure tests import the app through the app factory.

Tests:
- Add a pytest test using FastAPI TestClient that asserts GET /health returns 200 and the expected JSON.
- Add a config test verifying test defaults are available without real secrets.

Constraints:
- Do not connect to Supabase yet.
- Do not implement database logic yet.
- Keep this step focused on app startup and configuration.

Done criteria:
- All existing tests still pass.
- New health/config tests pass.
- FastAPI app can be run locally with uvicorn.
```

---

## Prompt 03 — Domain Models, Status Enum, Providers, and Schemas

```text
You are continuing the SME Bridge MVP from Prompt 02.

Goal:
Create the backend domain layer for utility bill state, providers, extracted LLM payloads, and internal DTOs. This should be pure Python with no database dependency.

Implement:
- apps/api/app/domain/statuses.py
  - UtilityBillStatus enum with:
    pending
    success
    flagged_low_confidence
    flagged_unreadable
    resolved_by_client

- apps/api/app/domain/providers.py
  - A normalized Malaysian utility provider master list containing at least:
    TNB
    Air Selangor
    Sarawak Energy
    Sabah Electricity
    Indah Water
  - normalize_provider_name(value: str) -> str
  - is_known_provider(value: str) -> bool

- apps/api/app/domain/schemas.py
  - Pydantic models for:
    ExtractedBillData
    ValidatedBillResult
    UtilityBillRecord
    AttachmentMetadata
  - ExtractedBillData should model:
    provider
    billing_period
    usage_value
    usage_unit
    confidence

Design notes:
- Confidence should be constrained to "high" or "low".
- Billing period should accept a YYYY-MM string for now.
- usage_value should be numeric but validation routing will be implemented in the next prompt.

Tests:
- Test all valid UtilityBillStatus values.
- Test provider normalization and known-provider matching.
- Test ExtractedBillData accepts valid payloads.
- Test ExtractedBillData rejects invalid confidence values.
- Test billing period shape where practical.

Constraints:
- Do not implement CO2e math yet.
- Do not implement the two-key validation yet.
- Do not add database code.

Done criteria:
- Domain tests pass.
- Existing tests pass.
- Domain layer remains importable without FastAPI app startup.
```

---

## Prompt 04 — CO2e Calculator and Two-Key Validation

```text
You are continuing the SME Bridge MVP from Prompt 03.

Goal:
Implement the pure business logic for CO2e calculation and the two-key validation state machine.

Implement:
- apps/api/app/domain/co2e.py
  - calculate_co2e(usage_value: Decimal | float, emission_factor: Decimal | float) -> Decimal
  - Ensure deterministic rounding behavior. Choose a decimal precision and document it in code comments.

- apps/api/app/domain/emission_factors.py
  - MVP emission factor config object or function.
  - Include electricity kWh factor loaded from Settings when called from runtime.
  - Also provide a pure default value for unit tests.

- apps/api/app/domain/validation.py
  - validate_extracted_bill(
      extracted: ExtractedBillData | None,
      emission_factor: Decimal
    ) -> ValidatedBillResult

Two-key logic:
- If extracted is None, return status flagged_unreadable.
- If required critical fields are missing or unusable, return flagged_unreadable.
- Generative key passes only when confidence == "high".
- Deterministic key passes only when:
  - usage_value is positive
  - provider is known
  - usage_unit is acceptable for MVP, starting with "kWh" for electricity
- If both keys pass:
  - status success
  - calculated_co2e populated
  - emission_factor_used populated
- If either key fails but JSON was parseable:
  - status flagged_low_confidence
  - include a reason list
- Do not return pending from this validator.

Tests:
- Perfect high-confidence TNB kWh payload becomes success.
- Low-confidence but otherwise valid payload becomes flagged_low_confidence.
- Unknown provider becomes flagged_low_confidence.
- Negative usage becomes flagged_low_confidence or flagged_unreadable according to your documented decision; prefer flagged_low_confidence if the JSON is parseable.
- Missing usage_value becomes flagged_unreadable.
- None input becomes flagged_unreadable.
- CO2e math is exact for at least two known inputs.

Constraints:
- Keep this pure and fast.
- No database, storage, image, or LLM code.

Done criteria:
- Tests fully cover routing to success, flagged_low_confidence, and flagged_unreadable.
- Existing tests pass.
```

---

## Prompt 05 — Supabase Database Migration SQL

```text
You are continuing the SME Bridge MVP from Prompt 04.

Goal:
Add SQL migration files for the Supabase PostgreSQL schema defined by the SME Bridge MVP. Do not wire live database access yet.

Create:
- apps/api/app/db/migrations/001_initial_schema.sql

Schema:
1. plcs
   - id uuid primary key default gen_random_uuid()
   - name text not null
   - created_at timestamptz not null default now()
   - updated_at timestamptz not null default now()

2. smes
   - id uuid primary key default gen_random_uuid()
   - plc_id uuid not null references plcs(id)
   - company_name text not null
   - created_at timestamptz not null default now()
   - updated_at timestamptz not null default now()

3. authorized_emails
   - id uuid primary key default gen_random_uuid()
   - sme_id uuid not null references smes(id)
   - email_address citext not null unique
   - created_at timestamptz not null default now()

4. utility_bills
   - id uuid primary key default gen_random_uuid()
   - sme_id uuid not null references smes(id)
   - status text not null
   - raw_file_url text not null
   - original_filename text
   - extracted_provider text
   - extracted_period text
   - extracted_usage numeric
   - extracted_usage_unit text
   - calculated_co2e numeric
   - emission_factor_used numeric
   - reviewer_id uuid null
   - validation_reasons jsonb not null default '[]'::jsonb
   - created_at timestamptz not null default now()
   - updated_at timestamptz not null default now()

Add:
- A CHECK constraint for utility_bills.status allowing only:
  pending
  success
  flagged_low_confidence
  flagged_unreadable
  resolved_by_client
- Useful indexes:
  - smes(plc_id)
  - authorized_emails(email_address)
  - utility_bills(sme_id)
  - utility_bills(status)
  - utility_bills(updated_at)
- updated_at trigger function and triggers where appropriate.

Also create:
- docs/database.md explaining the schema and status transitions.

Tests:
- Add a lightweight test that reads the migration file and asserts it contains the expected table names, status check values, and key indexes.
- Do not require a live Supabase database in CI.

Constraints:
- Do not implement repository code yet.
- Do not add seed data unless you put it in a separate optional file.

Done criteria:
- Migration file exists.
- Docs explain how to apply it in Supabase.
- Migration content test passes.
```

---

## Prompt 06 — Repository Contracts and In-Memory Repository

```text
You are continuing the SME Bridge MVP from Prompt 05.

Goal:
Create repository interfaces for database operations and an in-memory implementation for tests. Do not connect to Supabase yet.

Implement:
- apps/api/app/db/repositories.py

Define abstract/protocol-style contracts for:
- PlcRepository if needed later
- SmeRepository
- AuthorizedEmailRepository
- UtilityBillRepository

Minimum required operations:
- find_sme_by_authorized_email(email: str)
- create_pending_utility_bill(
    sme_id,
    raw_file_url,
    original_filename
  )
- get_bill(bill_id)
- list_bills_by_status(status, limit)
- mark_bill_processing_started or claim_next_pending_bill, whichever design you choose
- update_bill_extraction_result(...)
- mark_bill_unreadable(...)
- approve_bill(...)
- get_alert_counts(...)
- get_overview_metrics(...)
- list_bills_for_export(...)

Implement:
- apps/api/app/db/in_memory.py
  - InMemoryDatabase or individual in-memory repositories.
  - Must support the methods needed by upcoming webhook, worker, dashboard, review, and export routes.

Tests:
- Seed an in-memory SME and authorized email.
- Assert authorized email lookup works case-insensitively.
- Assert unknown email returns None.
- Assert creating a pending utility bill stores status pending.
- Assert claim_next_pending_bill returns one pending bill and avoids returning the same bill twice if your design marks it claimed.
- Assert updating extraction result persists fields.
- Assert approving bill sets status resolved_by_client and reviewer_id.

Constraints:
- Keep in-memory repo deterministic and simple.
- Do not use Supabase SDK yet.
- Do not implement API routes in this prompt.

Done criteria:
- Repository interfaces exist.
- In-memory implementation passes tests.
- Existing tests pass.
```

---

## Prompt 07 — Supabase Repository Implementation

```text
You are continuing the SME Bridge MVP from Prompt 06.

Goal:
Implement the real Supabase repository behind the same repository contracts, while keeping tests isolated from the live network by mocking the Supabase client.

Implement:
- apps/api/app/db/supabase_client.py
  - create_supabase_client(settings)
  - Keep all credentials loaded from Settings.
  - Do not create the client at import time.

- apps/api/app/db/supabase_repositories.py
  - SupabaseAuthorizedEmailRepository
  - SupabaseUtilityBillRepository
  - Any small shared helpers needed to map rows to domain schemas.

Required behavior:
- find_sme_by_authorized_email(email) queries authorized_emails joined or followed to smes.
- create_pending_utility_bill inserts a utility_bills row with pending status.
- claim_next_pending_bill fetches one pending row in a deterministic order.
- update_bill_extraction_result updates status and extracted fields.
- mark_bill_unreadable updates status flagged_unreadable with validation reasons.
- approve_bill updates status resolved_by_client, recalculates fields supplied by caller, and stamps reviewer_id.
- alert and overview methods provide data needed by dashboard APIs.
- export listing returns full audit fields.

Tests:
- Use mocks/fakes for Supabase SDK calls.
- Verify the correct table names are used.
- Verify pending bill insert payload contains status pending.
- Verify extraction updates include calculated_co2e and emission_factor_used.
- Verify unreadable update sets flagged_unreadable.
- Verify approve update sets resolved_by_client and reviewer_id.
- Verify no real network is required.

Constraints:
- Do not implement API routes yet.
- Do not implement storage yet.
- Keep all repository code behind the contract used by the in-memory version.

Done criteria:
- Supabase repository implementation passes mocked tests.
- In-memory repository tests still pass.
- No live credentials are required to run tests.
```

---

## Prompt 08 — Storage Contracts, Local Storage, and Supabase Storage

```text
You are continuing the SME Bridge MVP from Prompt 07.

Goal:
Create a storage abstraction for raw utility bill attachments, with local and Supabase implementations.

Implement:
- apps/api/app/storage/base.py
  - StorageService protocol/abstract class with:
    save_raw_attachment(sme_id, bill_id, filename, content_type, data) -> StoredFile
    get_file(file_url_or_path) -> bytes
    maybe_get_public_or_signed_url(file_url_or_path) -> str

- apps/api/app/storage/local_storage.py
  - Stores files under a configurable local directory, such as .local-storage.
  - Safe path handling to avoid path traversal.
  - Returns stable local file URLs/paths suitable for tests.

- apps/api/app/storage/supabase_storage.py
  - Uses Supabase Storage bucket from Settings.
  - Uploads to:
    utility-bills/raw/{sme_id}/{bill_id}/{safe_filename}
  - Returns storage path or public URL according to your design.
  - Do not create client at import time.

Tests:
- Local storage saves and reads bytes.
- Local storage sanitizes unsafe filenames.
- Local storage handles duplicate filenames deterministically, or documents overwrite behavior and tests it.
- Supabase storage uses mocked client calls and correct bucket/path.
- No test requires live Supabase.

Wire:
- Add a simple dependency factory module if useful, but do not yet expose routes.

Constraints:
- No webhook route yet.
- No image processing yet.

Done criteria:
- Storage tests pass.
- Repository tests still pass.
- README or docs mention local storage for tests/dev.
```

---

## Prompt 09 — Email Webhook Payload Parser

```text
You are continuing the SME Bridge MVP from Prompt 08.

Goal:
Implement parsing for inbound email webhook payloads independent of FastAPI route handling. This should support test fixtures from providers such as Postmark or SendGrid without locking the app to one provider.

Implement:
- apps/api/app/email/webhook_parser.py

Create:
- ParsedInboundEmail model:
  - from_email
  - subject
  - message_id, if available
  - attachments: list[ParsedAttachment]

- ParsedAttachment model:
  - filename
  - content_type
  - data bytes
  - size_bytes

Parser behavior:
- Accept a dict payload.
- Support at least one provider-shaped fixture, preferably Postmark-style:
  - From
  - Subject
  - MessageID
  - Attachments with Name, ContentType, Content base64
- Optionally support SendGrid-style if straightforward.
- Decode base64 attachment content.
- Ignore inline attachments unless explicitly marked as regular attachments, if the provider differentiates them.
- Reject or skip attachments with missing filename/content.
- Normalize from_email to lowercase.

Tests:
- Parse valid payload with one PDF attachment.
- Parse payload with five JPEG attachments.
- Missing From raises a controlled parser error.
- Invalid base64 attachment raises or skips according to a documented decision.
- Empty attachment list returns parsed email with zero attachments.
- From email is normalized.

Constraints:
- Do not implement authorization.
- Do not save files.
- Do not add FastAPI route yet.

Done criteria:
- Parser is fully unit tested.
- No network or storage dependency is introduced.
```

---

## Prompt 10 — Authorized Sender Check and Bounce Abstraction

```text
You are continuing the SME Bridge MVP from Prompt 09.

Goal:
Implement email sender authorization and a bounce/notification abstraction for unauthorized senders.

Implement:
- apps/api/app/email/authorization.py
  - EmailAuthorizationService
  - authorize_sender(from_email) -> AuthorizedSender | None
  - Uses the repository contract from earlier prompts.

- apps/api/app/email/bounce.py
  - BounceEmailService protocol/abstract class.
  - NoopBounceEmailService for tests/dev.
  - Method:
    send_unauthorized_sender_notice(to_email: str) -> None

Behavior:
- Email matching must be case-insensitive.
- Unknown sender returns None.
- Known sender returns SME id and company information needed by webhook route.
- Unauthorized sender should trigger the bounce service but should not raise an exception that would cause webhook retries.

Tests:
- Known authorized email returns SME info.
- Unknown email returns None.
- Case-insensitive email works.
- Bounce service fake records unauthorized notices.
- Bounce failure is caught/logged or otherwise does not break the webhook flow; document your decision.

Constraints:
- Do not implement the FastAPI webhook route yet.
- Do not send real email.
- Keep service code independent of provider-specific payload parsing.

Done criteria:
- Authorization tests pass.
- Bounce behavior is testable without network.
```

---

## Prompt 11 — Incoming Email Webhook Route with Multiple Attachments

```text
You are continuing the SME Bridge MVP from Prompt 10.

Goal:
Implement POST /webhook/incoming-email. The route must parse inbound email payloads, authorize the sender, save each attachment, create pending utility bill rows, and return quickly.

Implement:
- apps/api/app/api/routes/email_webhook.py
  - POST /webhook/incoming-email

Route behavior:
1. Accept JSON payload.
2. Parse it with the webhook parser.
3. Authorize the From email.
4. If unauthorized:
   - call bounce service
   - return 200 with a response indicating ignored/unauthorized
   - do not create utility_bills
   - do not save attachments
5. If authorized:
   - for each attachment:
     - create a pending utility_bills record or reserve an id as needed
     - save raw attachment to storage
     - ensure the bill record contains raw_file_url
   - return 200 quickly with count of accepted attachments.

Important design point:
The final implementation must ensure each attachment creates one distinct utility_bills row. If the repository cannot create a row before knowing raw_file_url, add a repository method that supports creating with a generated id, or create a clean two-step flow. Keep it tested.

Wire:
- Register route in create_app().
- Add dependency factories for repository, storage, authorization service, and bounce service.
- Tests may override dependencies with in-memory/fake implementations.

Tests:
- Authorized email with one attachment creates one pending bill and stores file.
- Authorized email with five JPEG attachments creates five pending bills.
- Unauthorized email returns 200, sends bounce notice, stores no files, creates no bills.
- Invalid payload returns an appropriate 400 without crashing.
- Empty attachment list returns 200 with accepted count 0 and creates no bills.
- Verify route does not invoke LLM or worker code.

Constraints:
- Do not implement background processing yet.
- Do not block on extraction.
- Do not require live Supabase.

Done criteria:
- Webhook route tests pass using FastAPI TestClient.
- Existing tests pass.
- docs/architecture.md is updated with webhook lifecycle.
```

---

## Prompt 12 — Worker Skeleton and Pending Bill Claim Flow

```text
You are continuing the SME Bridge MVP from Prompt 11.

Goal:
Create the background worker skeleton that claims pending bills and delegates processing. Do not implement file conversion, image processing, or LLM extraction yet.

Implement:
- apps/api/app/processing/worker.py

Create:
- ProcessingWorker
  - process_one() -> ProcessOneResult
  - process_until_empty(max_items: int | None = None) -> WorkerRunResult

Create:
- BillProcessor protocol/class with:
  - process_bill(bill: UtilityBillRecord) -> None

Behavior:
- process_one claims one pending bill from the repository.
- If no pending bill exists, return a no-work result.
- If a bill exists, pass it to BillProcessor.
- If BillProcessor raises a controlled exception, the worker logs and marks bill unreadable or delegates error handling according to your design.
- Worker should process one bill at a time to respect the local GPU constraint.

Add:
- A CLI entry point or script, such as:
  python -m app.processing.worker --once
  python -m app.processing.worker --max-items 10
  It may be a placeholder wired to dependency factories.

Tests:
- No pending bills returns no-work result.
- One pending bill is claimed and passed to fake processor.
- Multiple pending bills are processed sequentially with process_until_empty.
- Processor exception does not crash the entire worker loop.
- Same bill is not processed twice in the same run.

Constraints:
- Do not implement actual extraction yet.
- Do not use Celery.
- Keep this worker compatible with a future Celery replacement.

Done criteria:
- Worker tests pass.
- Webhook tests still pass.
```

---

## Prompt 13 — File Loading and PDF/Image Normalization

```text
You are continuing the SME Bridge MVP from Prompt 12.

Goal:
Implement file loading and conversion into page images suitable for preprocessing. Handle corrupted or password-protected PDFs gracefully.

Implement:
- apps/api/app/processing/file_loader.py
  - load_raw_file(storage, raw_file_url) -> bytes

- apps/api/app/processing/pdf_converter.py
  - file_to_page_images(filename, content_type, data) -> list[PIL.Image.Image]

Behavior:
- If content type or filename indicates PDF:
  - Use pdf2image to convert to page images.
  - Return one PIL image per page.
  - If conversion fails, raise a controlled UnreadableFileError.
- If content type or filename indicates PNG/JPG/JPEG:
  - Load as PIL image.
  - Return a single-image list.
  - If loading fails, raise UnreadableFileError.
- Unsupported file types raise UnreadableFileError.
- Do not auto-crop.
- Do not invoke LLM.

Tests:
- Valid PNG bytes load as one page image.
- Valid JPEG bytes load as one page image.
- Unsupported file type raises UnreadableFileError.
- Corrupted image bytes raise UnreadableFileError.
- Mock pdf2image to verify PDF conversion path returns multiple pages.
- Mock pdf2image failure and assert UnreadableFileError.

Dependencies:
- Add Pillow.
- Add pdf2image if not already present.
- Document system dependency for poppler in README or docs.

Constraints:
- Keep tests fast and avoid large binary fixtures.
- Do not add image preprocessing yet.

Done criteria:
- File conversion tests pass.
- Worker still uses a fake processor; no full pipeline yet.
```

---

## Prompt 14 — Image Preprocessing for GPU Protection

```text
You are continuing the SME Bridge MVP from Prompt 13.

Goal:
Implement deterministic image preprocessing that respects the MVP GPU protection protocol.

Implement:
- apps/api/app/processing/image_preprocessor.py

Function:
- preprocess_page_image(image: PIL.Image.Image, max_dimension: int = 1024) -> PIL.Image.Image

Behavior:
- Resize image so width and height are both <= max_dimension.
- Preserve aspect ratio.
- Convert to grayscale.
- Apply adaptive thresholding or a reasonable local/global thresholding fallback.
- Do not auto-crop backgrounds.
- Return a PIL image suitable for LLM input.
- Provide helper to encode processed image to PNG bytes.

Tests:
- Large landscape image is resized so max dimension is 1024.
- Large portrait image is resized so max dimension is 1024.
- Small image is not enlarged.
- Output mode is grayscale or binary according to your implementation.
- Aspect ratio is approximately preserved.
- Encoding helper returns PNG bytes.
- No crop occurs; dimensions after resize should match scale expectations.

Constraints:
- No LLM invocation yet.
- No database updates yet.
- Keep preprocessing deterministic.

Done criteria:
- Image preprocessing tests pass.
- README mentions max 1024px preprocessing rule.
```

---

## Prompt 15 — LLM Prompt Builder, Interface, and Fake LLM

```text
You are continuing the SME Bridge MVP from Prompt 14.

Goal:
Create the LLM extraction abstraction and prompt builder, with a fake implementation for tests.

Implement:
- apps/api/app/processing/llm_prompt.py
  - build_bill_extraction_prompt() -> str

Prompt requirements:
- Instruct the model to inspect a Malaysian utility bill image.
- Instruct the model to return only strict JSON.
- JSON shape must be:
  {
    "provider": "TNB",
    "billing_period": "YYYY-MM",
    "usage_value": 450,
    "usage_unit": "kWh",
    "confidence": "high"
  }
- Mention confidence must be "high" or "low".
- Mention that if unreadable, confidence should be "low" and fields should be best-effort/null if allowed by schema.

Implement:
- apps/api/app/processing/llm_client.py
  - LLMClient protocol with:
    extract_bill_data(image_png_bytes: bytes, prompt: str) -> str

- FakeLLMClient for tests:
  - Can be initialized with a queue/list of JSON strings or exceptions.
  - Returns one response per call.

Tests:
- Prompt contains strict JSON instruction.
- Prompt contains required keys.
- Prompt forbids non-JSON prose.
- FakeLLMClient returns queued responses in order.
- FakeLLMClient can simulate an exception.

Constraints:
- Do not implement Ollama/Gemma HTTP client yet.
- Do not parse JSON yet.
- Do not wire to processor yet.

Done criteria:
- LLM abstraction tests pass.
- No real model is needed.
```

---

## Prompt 16 — Ollama/Gemma Client Implementation

```text
You are continuing the SME Bridge MVP from Prompt 15.

Goal:
Implement the real local Gemma/Ollama client behind the LLMClient interface while keeping tests mocked.

Implement:
- In apps/api/app/processing/llm_client.py or a separate ollama_client.py:
  - OllamaGemmaClient

Behavior:
- Reads base URL and model name from Settings.
- Sends image and prompt to Ollama or the selected local inference endpoint.
- Returns the raw text response.
- Sets reasonable request timeout.
- Does not crash on non-200 responses; raises a controlled LLMInferenceError.
- Does not import heavy GPU libraries at module import time.

Tests:
- Mock HTTP client and assert request includes:
  - model name
  - prompt
  - image payload or expected image encoding
- Mock successful response returns text.
- Mock non-200 response raises LLMInferenceError.
- Mock timeout raises LLMInferenceError.
- No test requires local Ollama to be installed or running.

Docs:
- Update README or docs/local-llm.md with:
  - how to configure OLLAMA_BASE_URL
  - how to configure GEMMA_MODEL_NAME
  - how to run the API without the real LLM using FakeLLMClient in tests

Constraints:
- Do not wire real client into production dependency factory unless config makes it safe.
- Do not implement extraction parsing yet.

Done criteria:
- Ollama client tests pass with mocked HTTP.
- Existing fake LLM tests still pass.
```

---

## Prompt 17 — Extraction JSON Parser and Multi-Page Aggregation

```text
You are continuing the SME Bridge MVP from Prompt 16.

Goal:
Parse raw LLM responses into ExtractedBillData and aggregate multiple page outputs into one best candidate.

Implement:
- apps/api/app/processing/extraction_parser.py

Functions:
- parse_llm_extraction(raw_text: str) -> ExtractedBillData | None
- aggregate_page_extractions(extractions: list[ExtractedBillData | None]) -> ExtractedBillData | None

Parser behavior:
- Accept strict JSON.
- Tolerate minor wrapping such as markdown code fences if practical.
- Return None for broken JSON.
- Return None if required fields are absent.
- Convert numeric usage_value safely.
- Do not silently invent missing values.

Aggregation behavior:
- Prefer high-confidence extractions over low-confidence.
- Prefer known providers over unknown providers.
- Prefer positive usage values.
- If multiple high-confidence valid-looking candidates exist, choose the first deterministic candidate and document the rule.
- If all pages fail, return None.
- Keep aggregation deterministic.

Tests:
- Parses valid strict JSON.
- Parses JSON inside a code fence if supported.
- Broken JSON returns None.
- Missing usage returns None.
- Low-confidence valid JSON parses.
- Aggregation chooses high confidence over low confidence.
- Aggregation chooses known provider over unknown provider.
- Aggregation returns None when all pages are None.

Constraints:
- Do not update database here.
- Do not invoke image preprocessing or LLM here.
- Keep functions pure.

Done criteria:
- Parser and aggregation tests pass.
- Existing validation tests still pass.
```

---

## Prompt 18 — Full Bill Processing State Machine

```text
You are continuing the SME Bridge MVP from Prompt 17.

Goal:
Implement the full BillProcessor that loads a raw bill, converts pages, preprocesses each page, calls the LLM sequentially, parses and aggregates outputs, validates with two-key logic, calculates CO2e, and updates the utility_bills row.

Implement:
- apps/api/app/processing/processor.py
  - UtilityBillProcessor

Dependencies:
- UtilityBillRepository
- StorageService
- LLMClient
- Settings or emission factor provider

Processing flow:
1. Read raw file bytes from storage using bill.raw_file_url.
2. Convert PDF/image into page images.
3. For each page, sequentially:
   - preprocess image to max 1024px
   - encode to PNG bytes
   - build prompt
   - call LLMClient.extract_bill_data
   - parse response
   - collect extraction
   - clear GPU cache through a helper after each page, even in tests this can be a no-op
4. Aggregate page extractions.
5. Run two-key validation.
6. If success:
   - update bill to status success
   - save extracted provider, period, usage, unit, calculated_co2e, emission_factor_used
7. If flagged_low_confidence:
   - update bill to status flagged_low_confidence
   - save any extracted fields that exist
   - save validation reasons
8. If flagged_unreadable:
   - mark bill flagged_unreadable with reasons

Tests:
- Single-page valid extraction results in success update.
- Low-confidence extraction results in flagged_low_confidence update.
- Broken JSON results in flagged_unreadable.
- Multi-page bill processes pages sequentially and aggregates best extraction.
- LLM is called once per page.
- GPU cleanup helper is called after every page.
- Processor uses repository update methods rather than mutating records directly.

Constraints:
- Use FakeLLMClient and local/in-memory storage in tests.
- Do not require real Supabase.
- Do not require real Ollama.
- Do not implement OOM-specific handling yet; general errors may be covered but the next prompt will harden it.

Done criteria:
- Processor tests pass.
- Worker can now be tested with the real UtilityBillProcessor using fakes.
- Existing webhook route remains non-blocking and does not invoke this processor.
```

---

## Prompt 19 — OOM, Corrupted File, and Hardware Error Hardening

```text
You are continuing the SME Bridge MVP from Prompt 18.

Goal:
Harden the processing pipeline for edge cases from the technical spec: GPU OOM crashes, corrupted files, password-protected PDFs, unsupported files, and unexpected LLM failures.

Implement:
- apps/api/app/processing/errors.py if not already present.
- Controlled exception types:
  - UnreadableFileError
  - LLMInferenceError
  - ProcessingHardwareError or similar

Implement:
- apps/api/app/processing/gpu.py
  - clear_gpu_cache() -> None
  - Should try to import torch only inside the function.
  - If torch is unavailable, no-op.
  - If CUDA is unavailable, no-op.
  - If torch.cuda.empty_cache fails, log but do not crash.

Update UtilityBillProcessor:
- Corrupted image/PDF or password-protected PDF:
  - bypass LLM
  - mark flagged_unreadable
- LLM inference failure:
  - mark flagged_unreadable unless there is a better parseable previous page result; document decision.
- GPU OOM-like errors:
  - call clear_gpu_cache()
  - mark flagged_unreadable
  - do not crash worker loop
- Unexpected exceptions:
  - caught at worker boundary
  - bill marked flagged_unreadable with generic reason
  - exception logged

Tests:
- Corrupted file marks bill flagged_unreadable and does not call LLM.
- Unsupported file marks bill flagged_unreadable.
- Simulated LLMInferenceError marks bill flagged_unreadable.
- Simulated OOM exception calls clear_gpu_cache and marks unreadable.
- clear_gpu_cache no-ops safely if torch is not installed.
- Worker continues to next bill after one processing failure.

Docs:
- Add docs/hardware.md with:
  - sequential page processing
  - 1024px resizing
  - GPU cache clearing
  - manual VRAM stress test using nvidia-smi

Done criteria:
- Hardening tests pass.
- Worker loop remains stable after failures.
```

---

## Prompt 20 — Dashboard Alerts and Overview APIs

```text
You are continuing the SME Bridge MVP from Prompt 19.

Goal:
Implement read-only dashboard APIs for alert counts and impact overview.

Implement:
- apps/api/app/api/routes/dashboard.py

Endpoints:
1. GET /dashboard/alerts
   Returns:
   {
     "flagged_low_confidence": number,
     "flagged_unreadable": number,
     "total_requiring_review": number
   }

2. GET /dashboard/overview
   Returns:
   {
     "total_scope3_co2e_ytd": number,
     "breakdown": {
       "electricity": number,
       "water": number
     }
   }

Repository:
- Use repository methods from earlier prompts.
- If needed, extend repository contracts and both in-memory and Supabase implementations.
- For MVP, electricity/water breakdown can be inferred from usage_unit/provider where available. Document the rule.

Auth:
- Add a placeholder current-user dependency if needed, but do not build full auth yet.
- Ensure future PLC admin scoping can be added.
- Tests may use a fake user.

Tests:
- Alerts count flagged_low_confidence and flagged_unreadable.
- total_requiring_review is the sum of both.
- Overview sums successful and resolved_by_client CO2e values.
- Pending/unreadable records are excluded from total CO2e.
- Endpoint tests use FastAPI TestClient and in-memory repo.

Constraints:
- Do not implement frontend yet.
- Do not implement review approval yet.
- Keep response schemas typed.

Done criteria:
- Dashboard API tests pass.
- Existing webhook and processor tests pass.
```

---

## Prompt 21 — Bill Detail and HITL Approval APIs

```text
You are continuing the SME Bridge MVP from Prompt 20.

Goal:
Implement the backend APIs needed by the Human-in-the-Loop verification UI.

Implement endpoints:
1. GET /bills/{bill_id}
   Returns:
   - bill id
   - SME id/company name if available
   - status
   - raw_file_url or signed display URL
   - extracted_provider
   - extracted_period
   - extracted_usage
   - extracted_usage_unit
   - calculated_co2e
   - emission_factor_used
   - validation_reasons
   - updated_at

2. POST /bills/{bill_id}/approve
   Request:
   {
     "provider": "TNB",
     "billing_period": "2026-01",
     "usage_value": 500,
     "usage_unit": "kWh"
   }

Behavior:
- Validate submitted values.
- Recalculate CO2e server-side using the configured emission factor.
- Update bill:
  - status resolved_by_client
  - reviewer_id from current user dependency
  - extracted fields updated to reviewed values
  - calculated_co2e updated
  - emission_factor_used saved
- Return updated bill.

Auth:
- Implement a simple current-user dependency that can be overridden in tests.
- It should return a user id suitable for reviewer_id.
- Do not implement full Supabase Auth unless already available.

Tests:
- GET bill detail returns expected bill.
- GET missing bill returns 404.
- POST approve updates status to resolved_by_client.
- POST approve stamps reviewer_id.
- POST approve recalculates CO2e; it does not trust client-sent CO2e.
- Invalid usage_value returns 422 or 400.
- Unknown provider returns validation error or flagged behavior according to your documented approval rules; prefer rejecting unknown provider for manual approval.

Constraints:
- Do not implement frontend yet.
- Do not implement exports yet.

Done criteria:
- HITL API tests pass.
- Dashboard API tests still pass.
```

---

## Prompt 22 — CSV and XLSX Export APIs

```text
You are continuing the SME Bridge MVP from Prompt 21.

Goal:
Implement export generation for Bursa CSI-style CSV and raw XLSX audit archive.

Implement:
- apps/api/app/exports/csv_export.py
- apps/api/app/exports/xlsx_export.py
- apps/api/app/api/routes/exports.py

Endpoints:
1. GET /exports/csi.csv
   Returns text/csv or file response.

CSV columns:
- SME Name
- Period
- Usage
- Usage Unit
- CO2e
- S3 File Link

2. GET /exports/raw.xlsx
   Returns XLSX file response.

XLSX columns:
- utility_bill_id
- plc_id
- sme_id
- sme_name
- status
- provider
- period
- usage
- unit
- co2e
- emission_factor_used
- raw_file_url
- reviewer_id
- created_at
- updated_at

Behavior:
- Export success and resolved_by_client bills by default.
- Exclude pending unless an explicit include_all parameter is provided.
- Include raw_file_url for audit trail.
- Keep column order deterministic.
- Use pandas or openpyxl for XLSX.
- Use Python csv module or pandas for CSV.

Tests:
- CSV endpoint returns expected headers in exact order.
- CSV includes success/resolved rows.
- CSV excludes pending by default.
- XLSX endpoint returns a valid workbook.
- XLSX workbook has expected headers in exact order.
- Export generation works with in-memory repo.
- No live Supabase required.

Wire:
- Register exports route in FastAPI app.
- Update docs/exports.md with formats.

Constraints:
- Do not implement PDF summary yet.
- Do not implement frontend export modal yet.

Done criteria:
- CSV and XLSX export tests pass.
- Existing API tests pass.
```

---

## Prompt 23 — PDF Sustainability Summary Export

```text
You are continuing the SME Bridge MVP from Prompt 22.

Goal:
Implement the high-level Sustainability Summary PDF export for management.

Implement:
- apps/api/app/exports/pdf_export.py
- Extend apps/api/app/api/routes/exports.py with:
  GET /exports/summary.pdf

PDF contents:
- Title: SME Bridge Sustainability Summary
- Generated timestamp
- Total Scope 3 CO2e tracked YTD
- Electricity vs water breakdown
- Count of successful bills
- Count of resolved-by-client bills
- Count of bills requiring review
- Optional simple chart if practical, but text summary is acceptable for MVP if charting adds too much complexity.

Implementation options:
- Use reportlab or another lightweight PDF library.
- Keep PDF generation deterministic enough for tests.

Tests:
- Endpoint returns application/pdf.
- PDF bytes begin with %PDF.
- PDF generation does not crash with zero data.
- PDF generation includes summary values in a testable way, either by extracting text with a test utility or by testing the summary model before rendering.

Docs:
- Update docs/exports.md with PDF description.

Constraints:
- Do not implement frontend yet.
- Avoid large visual complexity.
- Keep chart generation optional and well-tested if added.

Done criteria:
- PDF export tests pass.
- CSV/XLSX export tests still pass.
```

---

## Prompt 24 — Frontend Shell and Typed API Client

```text
You are continuing the SME Bridge MVP from Prompt 23.

Goal:
Create the frontend application shell, routing structure, and typed API client. Do not build the full dashboard UI yet.

Implement in apps/web:
- React Router or a simple route structure for:
  - / dashboard
  - /bills/:billId review page placeholder
  - /exports placeholder
- src/api/types.ts with TypeScript types matching backend responses:
  - DashboardAlerts
  - DashboardOverview
  - UtilityBillDetail
  - ApproveBillRequest
- src/api/client.ts with functions:
  - getDashboardAlerts()
  - getDashboardOverview()
  - getBillDetail(billId)
  - approveBill(billId, payload)
  - downloadExport(kind)
- Environment variable for API base URL.

UI:
- App shell with nav links:
  - Dashboard
  - Exports
- Placeholder pages that render recognizable headings.

Tests:
- App renders dashboard heading.
- Navigation links exist.
- API client builds correct URLs, using fetch mocked in tests.
- API client handles non-OK responses by throwing a typed or clear error.

Constraints:
- Do not build actual charts yet.
- Do not build HITL form yet.
- Keep frontend code integrated through routes, not orphaned components.

Done criteria:
- Frontend tests pass.
- Backend tests still pass.
```

---

## Prompt 25 — Frontend Dashboard Alerts and Impact Overview

```text
You are continuing the SME Bridge MVP from Prompt 24.

Goal:
Build the main dashboard UI using the backend dashboard APIs.

Implement:
- components/AlertsBar.tsx
- components/ImpactOverview.tsx
- components/BreakdownChart.tsx or simple accessible breakdown visualization
- routes/DashboardPage.tsx

Behavior:
- On load, fetch /dashboard/alerts and /dashboard/overview.
- Show:
  - “X Bills Require Verification”
  - Total Scope 3 CO2e Tracked YTD
  - Electricity vs Water breakdown
- Show loading state.
- Show error state.
- Keep UI accessible with semantic headings and labels.

Testing:
- Mock API client.
- Test loading state.
- Test successful render of alert count and total CO2e.
- Test breakdown values render.
- Test error state.
- Ensure DashboardPage uses the components; do not leave components orphaned.

Constraints:
- Do not implement bill list unless needed for navigation.
- Do not implement HITL review yet.
- No real backend required for frontend tests.

Done criteria:
- Dashboard UI tests pass.
- App route renders the completed dashboard.
```

---

## Prompt 26 — Frontend HITL Review UI with Live CO2e Math

```text
You are continuing the SME Bridge MVP from Prompt 25.

Goal:
Build the Human-in-the-Loop review screen for flagged bills.

Implement:
- components/BillImageViewer.tsx
  - Displays raw bill image or file URL.
  - Supports basic zoom in/out.
  - Supports rotate left/right.
  - Keep implementation simple and testable.

- components/VerificationForm.tsx
  - Fields:
    provider
    billing_period
    usage_value
    usage_unit
  - Read-only calculated CO2e display.
  - Approve button.

- routes/ReviewBillPage.tsx
  - Fetches bill detail by billId.
  - Displays side-by-side layout:
    left: BillImageViewer
    right: VerificationForm
  - Pre-fills form from extracted bill fields.
  - Performs live CO2e math when usage_value changes.
  - Calls approveBill on submit.
  - Shows success state after approval.

Emission factor:
- Use the emission_factor_used from the bill if present.
- If missing, use a frontend config value matching backend MVP config.
- Backend remains authoritative on approval.

Tests:
- Review page loads bill detail and pre-fills fields.
- Changing usage from 450 to 500 updates live CO2e.
- Clicking approve calls API with reviewed values.
- Success state appears after approval.
- Image viewer zoom and rotate controls update UI state.
- Error state renders on failed fetch.
- Components are wired into ReviewBillPage; no orphaned components.

Constraints:
- Do not implement authentication UI.
- Do not trust frontend CO2e for persistence; backend recalculates.
- Keep layout responsive but simple.

Done criteria:
- HITL frontend tests pass.
- Dashboard tests still pass.
```

---

## Prompt 27 — Frontend Export Modal

```text
You are continuing the SME Bridge MVP from Prompt 26.

Goal:
Build the frontend export modal that lets users download CSI CSV, raw XLSX archive, and PDF sustainability summary.

Implement:
- components/ExportModal.tsx
- Integrate it into DashboardPage or ExportsPage.

Behavior:
- Modal has three export actions:
  1. CSI Prescribed Format CSV
  2. Raw Data Archive XLSX
  3. Sustainability Summary PDF
- Each action calls the API client downloadExport(kind).
- Show loading state while a download is being prepared.
- Show error state if download fails.
- For browser behavior, create a Blob URL and trigger download with a sensible filename:
  - sme-bridge-csi.csv
  - sme-bridge-raw-archive.xlsx
  - sme-bridge-summary.pdf

Tests:
- Modal opens and closes.
- Each export button calls the correct API client function.
- Successful download creates an anchor click or equivalent mocked behavior.
- Failed download shows an error.
- ExportModal is reachable from the app UI; it is not orphaned.

Constraints:
- Do not implement new backend endpoints.
- Use the endpoints already created in Prompts 22 and 23.

Done criteria:
- Export modal tests pass.
- Dashboard and review page tests still pass.
```

---

## Prompt 28 — End-to-End Integration, Deployment Docs, and Final Wiring

```text
You are continuing the SME Bridge MVP from Prompt 27.

Goal:
Wire the MVP together end to end, add integration tests for the core happy path and key failure paths, and document local deployment with Cloudflare Tunnel or Ngrok.

Backend integration tests:
Create tests that exercise the complete backend flow using fakes/in-memory implementations:
1. Seed PLC, SME, and authorized email.
2. POST /webhook/incoming-email with one valid attachment.
3. Assert one pending utility_bill is created.
4. Run worker process_one with FakeLLMClient returning valid high-confidence JSON.
5. Assert bill becomes success with calculated CO2e.
6. Call /dashboard/alerts and /dashboard/overview.
7. Call /exports/csi.csv and assert the bill is included.

Failure-path integration tests:
1. Unauthorized email:
   - webhook returns 200
   - no bill created
   - bounce service called
2. Corrupted attachment:
   - pending bill created
   - worker marks flagged_unreadable
3. Low-confidence LLM JSON:
   - worker marks flagged_low_confidence
   - dashboard alerts count it
4. Manual approval:
   - GET bill detail
   - POST approve
   - status becomes resolved_by_client
   - reviewer_id is stamped
   - CO2e is recalculated

Frontend integration tests:
- Use mocked API client or MSW.
- Verify dashboard can display overview and open export modal.
- Verify review page can fetch a flagged bill, edit usage, and approve.

Docs:
Update README and docs/deployment.md with:
- Required environment variables.
- How to run backend locally.
- How to run frontend locally.
- How to run worker once and continuously.
- How to apply Supabase migration.
- How to configure Supabase Storage bucket.
- How to configure Postmark/SendGrid webhook to POST /webhook/incoming-email.
- How to expose local FastAPI through Cloudflare Tunnel or Ngrok.
- How to configure local Ollama/Gemma.
- Manual VRAM stress test procedure with a dense 15-page PDF and nvidia-smi.
- Known MVP limitations.

Final cleanup:
- Ensure all routes are registered.
- Ensure dependency factories have safe test overrides.
- Ensure no code exists that is not reachable through app routes, worker, tests, or documented scripts.
- Run all backend tests.
- Run all frontend tests.
- Run lint/typecheck where configured.

Done criteria:
- End-to-end backend integration tests pass.
- Frontend integration tests pass.
- All existing tests pass.
- README documents a complete local MVP run.
- The system has no hanging or orphaned implementation pieces.
```

---

# 4. Final Implementation Notes

The safest implementation path is to keep the **business logic pure first**, then add infrastructure around it. The most important early tests are:

1. CO2e math.
2. Two-key validation.
3. Webhook authorization.
4. Multiple attachment handling.
5. Worker sequential processing.
6. Corrupted file and OOM failure behavior.
7. HITL approval recalculation.
8. Export column ordering.

The highest-risk areas are the local LLM integration, PDF conversion, and GPU memory behavior. That is why the prompts isolate those behind interfaces and fakes before introducing real Ollama/Gemma calls. This keeps the project testable even when the local RTX 3060 environment is unavailable.
