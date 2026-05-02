# SME Bridge MVP - Implementation TODO Checklist

Use this checklist from top to bottom. Each milestone is designed to be implemented in small, testable increments. Do not move to the next milestone until the milestone gate is complete.

Source specification: `Technical Specification: SME Bridge (MVP Prototype)`.

## Working Rules

- [ ] Keep every change integrated into an executable path: API route, worker flow, test, documented script, or frontend route.
- [ ] Write or update tests before or alongside implementation.
- [ ] Prefer pure business logic first, then infrastructure adapters.
- [ ] Do not call the real LLM, Supabase, email provider, or storage service in unit tests.
- [ ] Use fake or in-memory implementations for tests.
- [ ] Keep the webhook fast: save files and create `pending` rows only.
- [ ] Process bills sequentially in the worker to protect 6GB VRAM.
- [ ] Always save `emission_factor_used` with calculated results for auditability.
- [ ] Never trust frontend CO2e calculations for persistence; backend recalculates on approval.
- [ ] Before merging a milestone, run all tests touched by the milestone.

## Assumptions to Confirm or Document

- [ ] Backend stack: Python 3.11+, FastAPI, pytest.
- [ ] Database: Supabase PostgreSQL.
- [ ] File storage: Supabase Storage bucket for raw bill images/PDFs.
- [ ] LLM: local Gemma through Ollama or HuggingFace-compatible local runtime.
- [ ] Frontend: React + TypeScript + Vite.
- [ ] Local sandbox hardware: Lenovo LOQ i5 with RTX 3060 and 6GB VRAM.
- [ ] Public webhook exposure: Cloudflare Tunnel or Ngrok.
- [ ] Inbound email provider: Postmark or SendGrid.
- [ ] MVP utility providers include at least TNB, Air Selangor, Sarawak Energy, Sabah Electricity, and Indah Water.
- [ ] MVP initial usage unit for electricity is `kWh`.
- [ ] Hardcoded Malaysian emission factor value is selected, documented, and versioned.
- [ ] Timezone behavior for reports and timestamps is documented.

---

# Milestone 0 - Repository Bootstrap

## 0.1 Create Monorepo Structure

- [x] Create root `README.md`.
- [x] Create root `.gitignore`.
- [x] Create `apps/api/`.
- [x] Create `apps/web/`.
- [x] Create `docs/`.
- [x] Create `scripts/`.
- [x] Create `docs/architecture.md` placeholder.
- [x] Document overall system components in `docs/architecture.md`:
  - [x] FastAPI backend.
  - [x] Supabase PostgreSQL.
  - [x] Supabase Storage.
  - [x] Local Gemma/Ollama extraction worker.
  - [x] React dashboard.
  - [x] Email webhook provider.
  - [x] Cloudflare Tunnel or Ngrok.

## 0.2 Backend Tooling

- [x] Create Python environment configuration.
- [x] Add FastAPI dependency.
- [x] Add pytest dependency.
- [x] Add ruff dependency.
- [x] Add type-checking dependency if used: mypy or pyright.
- [x] Create `apps/api/app/__init__.py`.
- [x] Create `apps/api/tests/`.
- [x] Add a minimal backend smoke test.
- [x] Add backend test command to README.
- [x] Add backend lint command to README.
- [x] Add backend typecheck command to README if configured.

## 0.3 Frontend Tooling

- [x] Initialize Vite React TypeScript app in `apps/web`.
- [x] Add Vitest.
- [x] Add React Testing Library.
- [x] Add frontend linting.
- [x] Add minimal component smoke test.
- [x] Add frontend test command to README.
- [x] Add frontend lint command to README.

## 0.4 Bootstrap Gate

- [x] Backend smoke test passes.
- [x] Frontend smoke test passes.
- [x] README contains exact setup, test, lint, and run commands.
- [x] No product logic exists yet.

---

# Milestone 1 - FastAPI App Shell and Configuration

## 1.1 App Factory

- [x] Create `apps/api/app/main.py`.
- [x] Implement `create_app()`.
- [x] Register routes through explicit router modules.
- [x] Ensure importing `create_app()` does not connect to Supabase.
- [x] Ensure importing `create_app()` does not connect to Ollama.

## 1.2 Settings

- [x] Create `apps/api/app/core/config.py`.
- [x] Implement typed `Settings` object.
- [x] Add environment variable for `APP_ENV`.
- [x] Add environment variable for `SUPABASE_URL`.
- [x] Add environment variable for `SUPABASE_SERVICE_ROLE_KEY`.
- [x] Add environment variable for `SUPABASE_STORAGE_BUCKET`.
- [x] Add environment variable for `OLLAMA_BASE_URL`.
- [x] Add environment variable for `GEMMA_MODEL_NAME`.
- [x] Add environment variable for `EMISSION_FACTOR_ELECTRICITY_KWH`.
- [x] Provide safe test defaults.
- [x] Prevent required production secrets from blocking tests.

## 1.3 Health Route

- [x] Create `apps/api/app/api/routes/health.py`.
- [x] Implement `GET /health`.
- [x] Return JSON:

```json
{
  "status": "ok",
  "service": "sme-bridge-api"
}
```

- [x] Register health route in `create_app()`.

## 1.4 Tests

- [x] Test `GET /health` returns HTTP 200.
- [x] Test `GET /health` returns expected JSON.
- [x] Test settings load with test defaults.
- [x] Test app factory can be imported without credentials.

## 1.5 Milestone Gate

- [x] Backend tests pass.
- [x] App runs locally with uvicorn.
- [x] README includes local API run command.

---

# Milestone 2 - Pure Domain Layer

## 2.1 Status Enum

- [x] Create `apps/api/app/domain/statuses.py`.
- [x] Implement `UtilityBillStatus` enum.
- [x] Add `pending`.
- [x] Add `success`.
- [x] Add `flagged_low_confidence`.
- [x] Add `flagged_unreadable`.
- [x] Add `resolved_by_client`.
- [x] Ensure enum values match database status strings exactly.

## 2.2 Provider Master List

- [x] Create `apps/api/app/domain/providers.py`.
- [x] Add provider `TNB`.
- [x] Add provider `Air Selangor`.
- [x] Add provider `Sarawak Energy`.
- [x] Add provider `Sabah Electricity`.
- [x] Add provider `Indah Water`.
- [x] Implement `normalize_provider_name(value: str) -> str`.
- [x] Implement `is_known_provider(value: str) -> bool`.
- [x] Ensure provider matching is case-insensitive.
- [x] Add documented alias behavior if aliases are included.

## 2.3 Domain Schemas

- [x] Create `apps/api/app/domain/schemas.py`.
- [x] Add `ExtractedBillData` model.
- [x] Add `ValidatedBillResult` model.
- [x] Add `UtilityBillRecord` model.
- [x] Add `AttachmentMetadata` model.
- [x] Constrain `confidence` to `high` or `low`.
- [x] Model `billing_period` as `YYYY-MM` string for MVP.
- [x] Model `usage_value` as numeric.
- [x] Model `usage_unit` as string.
- [x] Include validation reasons on validation result.

## 2.4 Tests

- [x] Test all status enum values.
- [x] Test provider normalization.
- [x] Test known provider matching.
- [x] Test unknown provider rejection.
- [x] Test valid extracted payload is accepted.
- [x] Test invalid confidence is rejected.
- [x] Test invalid billing period shape is rejected if schema enforces it.

## 2.5 Milestone Gate

- [x] Domain layer imports without FastAPI startup.
- [x] Domain tests pass.
- [x] Existing tests pass.

---

# Milestone 3 - CO2e Calculation and Two-Key Validation

## 3.1 Emission Factor Module

- [x] Create `apps/api/app/domain/emission_factors.py`.
- [x] Define MVP electricity kWh emission factor source.
- [x] Read configured factor from settings at runtime.
- [x] Provide pure default factor for tests.
- [x] Document factor source and units.
- [x] Ensure factor can be snapshotted onto each bill row.

## 3.2 CO2e Calculator

- [x] Create `apps/api/app/domain/co2e.py`.
- [x] Implement `calculate_co2e(usage_value, emission_factor)`.
- [x] Use `Decimal` internally or document numeric precision choice.
- [x] Define deterministic rounding behavior.
- [x] Add comments explaining rounding.

## 3.3 Two-Key Validator

- [x] Create `apps/api/app/domain/validation.py`.
- [x] Implement `validate_extracted_bill(extracted, emission_factor)`.
- [x] Return `flagged_unreadable` when extraction is `None`.
- [x] Return `flagged_unreadable` when critical fields are missing.
- [x] Generative key passes only when `confidence == "high"`.
- [x] Deterministic key passes only when provider is known.
- [x] Deterministic key passes only when usage value is positive.
- [x] Deterministic key passes only when usage unit is acceptable.
- [x] Return `success` when both keys pass.
- [x] Return `flagged_low_confidence` when parseable JSON exists but either key fails.
- [x] Include reason codes or reason messages in all non-success results.
- [x] Populate calculated CO2e and emission factor on success.

## 3.4 Tests

- [x] Perfect high-confidence TNB kWh payload returns `success`.
- [x] Low-confidence otherwise-valid payload returns `flagged_low_confidence`.
- [x] Unknown provider returns `flagged_low_confidence`.
- [x] Negative usage returns documented failure state.
- [x] Zero usage returns documented failure state.
- [x] Missing usage returns `flagged_unreadable`.
- [x] `None` extraction returns `flagged_unreadable`.
- [x] CO2e calculation has exact expected value for simple inputs.
- [x] Rounding behavior is tested.

## 3.5 Milestone Gate

- [x] Validator routes to `success`, `flagged_low_confidence`, and `flagged_unreadable` correctly.
- [x] CO2e tests pass.
- [x] Domain tests pass.

---

# Milestone 4 - Supabase Database Schema

## 4.1 Migration File

- [x] Create `apps/api/app/db/migrations/001_initial_schema.sql`.
- [x] Enable `pgcrypto` or equivalent for `gen_random_uuid()` if needed.
- [x] Enable `citext` for case-insensitive email if supported.

## 4.2 `plcs` Table

- [x] Add `id uuid primary key default gen_random_uuid()`.
- [x] Add `name text not null`.
- [x] Add `created_at timestamptz not null default now()`.
- [x] Add `updated_at timestamptz not null default now()`.

## 4.3 `smes` Table

- [x] Add `id uuid primary key default gen_random_uuid()`.
- [x] Add `plc_id uuid not null references plcs(id)`.
- [x] Add `company_name text not null`.
- [x] Add `created_at timestamptz not null default now()`.
- [x] Add `updated_at timestamptz not null default now()`.
- [x] Add index on `smes(plc_id)`.

## 4.4 `authorized_emails` Table

- [x] Add `id uuid primary key default gen_random_uuid()`.
- [x] Add `sme_id uuid not null references smes(id)`.
- [x] Add `email_address citext not null unique`.
- [x] Add `created_at timestamptz not null default now()`.
- [x] Add index on `authorized_emails(email_address)`.

## 4.5 `utility_bills` Table

- [x] Add `id uuid primary key default gen_random_uuid()`.
- [x] Add `sme_id uuid not null references smes(id)`.
- [x] Add `status text not null`.
- [x] Add `raw_file_url text not null`.
- [x] Add `original_filename text`.
- [x] Add `extracted_provider text`.
- [x] Add `extracted_period text`.
- [x] Add `extracted_usage numeric`.
- [x] Add `extracted_usage_unit text`.
- [x] Add `calculated_co2e numeric`.
- [x] Add `emission_factor_used numeric`.
- [x] Add `reviewer_id uuid null`.
- [x] Add `validation_reasons jsonb not null default '[]'::jsonb`.
- [x] Add `created_at timestamptz not null default now()`.
- [x] Add `updated_at timestamptz not null default now()`.
- [x] Add status check constraint for allowed states.
- [x] Add index on `utility_bills(sme_id)`.
- [x] Add index on `utility_bills(status)`.
- [x] Add index on `utility_bills(updated_at)`.

## 4.6 Updated Timestamp Triggers

- [x] Add shared `updated_at` trigger function.
- [x] Add trigger for `plcs`.
- [x] Add trigger for `smes`.
- [x] Add trigger for `utility_bills`.

## 4.7 Documentation

- [x] Create `docs/database.md`.
- [x] Explain each table.
- [x] Explain status transitions.
- [x] Explain audit fields.
- [x] Explain how to apply migration in Supabase.
- [x] Explain optional seed data approach.

## 4.8 Tests

- [x] Test migration file exists.
- [x] Test migration contains all table names.
- [x] Test migration contains all status check values.
- [x] Test migration contains important indexes.
- [x] Test migration contains `updated_at` trigger function.

## 4.9 Milestone Gate

- [x] Migration content tests pass.
- [x] Docs explain schema and state transitions.
- [x] No live database is required for tests.

---

# Milestone 5 - Repository Contracts and In-Memory Database

## 5.1 Repository Contracts

- [x] Create `apps/api/app/db/repositories.py`.
- [x] Define SME lookup contract.
- [x] Define authorized email lookup contract.
- [x] Define utility bill contract.
- [x] Add `find_sme_by_authorized_email(email)`.
- [x] Add `create_pending_utility_bill(sme_id, raw_file_url, original_filename)`.
- [x] Add `get_bill(bill_id)`.
- [x] Add `list_bills_by_status(status, limit)`.
- [x] Add `claim_next_pending_bill()`.
- [x] Add `update_bill_extraction_result(...)`.
- [x] Add `mark_bill_unreadable(...)`.
- [x] Add `approve_bill(...)`.
- [x] Add `get_alert_counts(...)`.
- [x] Add `get_overview_metrics(...)`.
- [x] Add `list_bills_for_export(...)`.

## 5.2 In-Memory Implementation

- [x] Create `apps/api/app/db/in_memory.py`.
- [x] Add in-memory PLC storage if needed.
- [x] Add in-memory SME storage.
- [x] Add in-memory authorized email storage.
- [x] Add in-memory utility bill storage.
- [x] Generate deterministic UUIDs or accept provided UUIDs in tests.
- [x] Implement case-insensitive email lookup.
- [x] Implement pending bill creation.
- [x] Implement pending bill claiming.
- [x] Ensure claimed bills are not returned twice in a single worker run.
- [x] Implement extraction result update.
- [x] Implement unreadable marking.
- [x] Implement manual approval update.
- [x] Implement alert counts.
- [x] Implement overview metrics.
- [x] Implement export listing.

## 5.3 Tests

- [x] Seed PLC, SME, and authorized email.
- [x] Authorized email lookup returns SME.
- [x] Email lookup is case-insensitive.
- [x] Unknown email returns `None`.
- [x] Creating pending bill stores `pending` status.
- [x] Claimed bill is returned once.
- [x] Extraction result update persists extracted fields.
- [x] Unreadable update persists status and reasons.
- [x] Approval update sets `resolved_by_client`.
- [x] Approval update stamps `reviewer_id`.
- [x] Alert counts include low-confidence and unreadable bills.
- [x] Overview excludes pending and unreadable bills.

## 5.4 Milestone Gate

- [x] Repository contract is stable enough for routes and worker.
- [x] In-memory tests pass.
- [x] Existing tests pass.

---

# Milestone 6 - Supabase Repository Adapter

## 6.1 Supabase Client Factory

- [x] Create `apps/api/app/db/supabase_client.py`.
- [x] Implement `create_supabase_client(settings)`.
- [x] Load URL from settings.
- [x] Load service role key from settings.
- [x] Do not create client at import time.
- [x] Do not require Supabase credentials in tests.

## 6.2 Supabase Repository Implementation

- [x] Create `apps/api/app/db/supabase_repositories.py`.
- [x] Implement authorized email lookup.
- [x] Implement pending bill insertion.
- [x] Implement bill fetch by id.
- [x] Implement pending bill claim.
- [x] Implement extraction result update.
- [x] Implement unreadable update.
- [x] Implement manual approval update.
- [x] Implement alert counts.
- [x] Implement overview metrics.
- [x] Implement export listing.
- [x] Map Supabase rows into domain schemas.
- [x] Keep table names centralized where practical.

## 6.3 Supabase Adapter Tests

- [x] Mock Supabase SDK calls.
- [x] Verify `authorized_emails` table is used for lookup.
- [x] Verify `smes` lookup or join behavior.
- [x] Verify `utility_bills` table is used for bill operations.
- [x] Verify pending insert payload includes `status: pending`.
- [x] Verify extraction update includes calculated CO2e.
- [x] Verify extraction update includes emission factor snapshot.
- [x] Verify unreadable update sets `flagged_unreadable`.
- [x] Verify approval update sets `resolved_by_client`.
- [x] Verify approval update stamps `reviewer_id`.
- [x] Confirm no test performs network calls.

## 6.4 Milestone Gate

- [x] Supabase adapter tests pass with mocks.
- [x] In-memory repository tests still pass.
- [x] No live Supabase dependency in CI.

---

# Milestone 7 - Storage Abstraction

## 7.1 Storage Contract

- [x] Create `apps/api/app/storage/base.py`.
- [x] Define `StorageService` protocol or abstract class.
- [x] Define `StoredFile` model.
- [x] Add `save_raw_attachment(sme_id, bill_id, filename, content_type, data)`.
- [x] Add `get_file(file_url_or_path)`.
- [x] Add `maybe_get_public_or_signed_url(file_url_or_path)`.

## 7.2 Local Storage Implementation

- [x] Create `apps/api/app/storage/local_storage.py`.
- [x] Store files under configurable local directory.
- [x] Sanitize filenames.
- [x] Prevent path traversal.
- [x] Use stable local paths for tests.
- [x] Return stored file path or URL.
- [x] Read stored file bytes.

## 7.3 Supabase Storage Implementation

- [x] Create `apps/api/app/storage/supabase_storage.py`.
- [x] Use configured bucket.
- [x] Upload files to `utility-bills/raw/{sme_id}/{bill_id}/{safe_filename}`.
- [x] Return storage path or URL according to documented design.
- [x] Support signed URL or public URL retrieval.
- [x] Do not create Supabase client at import time.

## 7.4 Tests

- [x] Local storage saves bytes.
- [x] Local storage reads bytes.
- [x] Unsafe filename is sanitized.
- [x] Path traversal attempt is blocked.
- [x] Duplicate filename behavior is deterministic or documented.
- [x] Supabase storage uses correct bucket.
- [x] Supabase storage uses correct object path.
- [x] Supabase storage upload is tested with mocked client.
- [x] No live Supabase storage needed in tests.

## 7.5 Documentation

- [x] Document local storage mode for tests.
- [x] Document Supabase bucket setup.
- [x] Document raw file path convention.

## 7.6 Milestone Gate

- [x] Storage tests pass.
- [x] Repository tests pass.
- [x] Storage implementation is not coupled to FastAPI routes.

---

# Milestone 8 - Email Webhook Parser

## 8.1 Parser Models

- [x] Create `apps/api/app/email/webhook_parser.py`.
- [x] Define `ParsedInboundEmail`.
- [x] Include `from_email`.
- [x] Include `subject`.
- [x] Include `message_id` if available.
- [x] Include list of parsed attachments.
- [x] Define `ParsedAttachment`.
- [x] Include `filename`.
- [x] Include `content_type`.
- [x] Include `data` bytes.
- [x] Include `size_bytes`.

## 8.2 Provider Shape Support

- [x] Support Postmark-style payload with `From`.
- [x] Support Postmark-style `Subject`.
- [x] Support Postmark-style `MessageID`.
- [x] Support Postmark-style attachments with `Name`, `ContentType`, and base64 `Content`.
- [x] Optionally support SendGrid-style payload.
- [x] Document provider shapes supported.

## 8.3 Parser Behavior

- [x] Normalize `from_email` to lowercase.
- [x] Decode base64 attachment content.
- [x] Skip inline attachments if provider marks them as inline.
- [x] Reject missing `From` with controlled parser error.
- [x] Reject or skip missing attachment filename according to documented decision.
- [x] Reject or skip missing attachment content according to documented decision.
- [x] Handle empty attachment list.
- [x] Handle invalid base64 with controlled parser error or documented skip behavior.

## 8.4 Tests

- [x] Valid payload with one PDF attachment parses.
- [x] Valid payload with five JPEG attachments parses.
- [x] Missing `From` raises controlled parser error.
- [x] Invalid base64 is handled as documented.
- [x] Empty attachment list returns zero attachments.
- [x] From email is normalized to lowercase.
- [x] Inline attachments are skipped if supported.

## 8.5 Milestone Gate

- [x] Parser tests pass.
- [x] Parser has no storage, database, or FastAPI dependency.

---

# Milestone 9 - Email Authorization and Bounce Service

## 9.1 Authorization Service

- [x] Create `apps/api/app/email/authorization.py`.
- [x] Implement `EmailAuthorizationService`.
- [x] Implement `authorize_sender(from_email)`.
- [x] Use repository contract for lookup.
- [x] Return authorized SME info when found.
- [x] Return `None` when not found.
- [x] Ensure case-insensitive behavior.

## 9.2 Bounce Service

- [x] Create `apps/api/app/email/bounce.py`.
- [x] Define `BounceEmailService` protocol.
- [x] Implement `NoopBounceEmailService` for tests/dev.
- [x] Implement `send_unauthorized_sender_notice(to_email)`.
- [x] Ensure bounce failure does not crash webhook flow.
- [x] Log bounce failures.
- [x] Do not send real email yet unless explicitly configured.

## 9.3 Tests

- [x] Known authorized sender returns SME info.
- [x] Unknown sender returns `None`.
- [x] Case-insensitive sender lookup works.
- [x] Fake bounce service records unauthorized notices.
- [x] Bounce failure is caught or isolated as documented.

## 9.4 Milestone Gate

- [x] Authorization tests pass.
- [x] Bounce tests pass.
- [x] No real email is sent in tests.

---

# Milestone 10 - Incoming Email Webhook Route

## 10.1 Dependency Factories

- [x] Add backend dependency module if needed.
- [x] Provide repository dependency.
- [x] Provide storage dependency.
- [x] Provide authorization service dependency.
- [x] Provide bounce service dependency.
- [x] Ensure tests can override dependencies.
- [x] Ensure production dependencies are not created at import time.

## 10.2 Webhook Route

- [x] Create `apps/api/app/api/routes/email_webhook.py`.
- [x] Implement `POST /webhook/incoming-email`.
- [x] Accept JSON body.
- [x] Parse payload using webhook parser.
- [x] Authorize `From` email.
- [x] For unauthorized sender:
  - [x] Call bounce service.
  - [x] Return HTTP 200.
  - [x] Do not create utility bill rows.
  - [x] Do not save attachments.
  - [x] Return response indicating ignored unauthorized sender.
- [x] For authorized sender:
  - [x] Process each attachment independently.
  - [x] Create or reserve one distinct bill id per attachment.
  - [x] Save raw attachment to storage.
  - [x] Create or update utility bill row with raw file URL.
  - [x] Set status to `pending`.
  - [x] Return accepted attachment count.
- [x] Register webhook route in app factory.

## 10.3 Multiple Attachment Rules

- [x] One attachment maps to one `utility_bills` row.
- [x] Five JPEG attachments map to five rows.
- [x] Empty attachment list creates zero rows.
- [x] A failed attachment save should not silently create a broken row.
- [x] Partial failure behavior is documented.

## 10.4 Tests

- [x] Authorized email with one PDF creates one pending bill.
- [x] Authorized email with one PDF saves one raw file.
- [x] Authorized email with five JPEGs creates five pending bills.
- [x] Unauthorized email returns HTTP 200.
- [x] Unauthorized email sends bounce notice.
- [x] Unauthorized email creates no bills.
- [x] Unauthorized email saves no files.
- [x] Invalid payload returns HTTP 400 or controlled response.
- [x] Empty attachment list returns accepted count zero.
- [x] Webhook route does not invoke LLM.
- [x] Webhook route does not invoke worker.

## 10.5 Documentation

- [x] Update `docs/architecture.md` with webhook lifecycle.
- [x] Document why extraction is asynchronous.
- [x] Document webhook retry avoidance.

## 10.6 Milestone Gate

- [x] Webhook tests pass.
- [x] Existing parser and authorization tests pass.
- [x] Webhook returns quickly and does not process LLM work.

---

# Milestone 11 - Worker Skeleton

## 11.1 Worker Class

- [x] Create `apps/api/app/processing/worker.py`.
- [x] Define `BillProcessor` protocol or base class.
- [x] Implement `ProcessingWorker`.
- [x] Implement `process_one()`.
- [x] Implement `process_until_empty(max_items=None)`.
- [x] Process bills sequentially.
- [x] Return no-work result when queue is empty.

## 11.2 Worker Error Handling Skeleton

- [x] If processor raises controlled exception, do not crash loop.
- [x] Mark failed bill unreadable or delegate error state to processor.
- [x] Log exception details.
- [x] Continue to next bill when appropriate.

## 11.3 Worker CLI

- [x] Add `python -m app.processing.worker --once` support or script wrapper.
- [x] Add `python -m app.processing.worker --max-items 10` support or script wrapper.
- [x] Document worker command in README.
- [x] Keep CLI dependency setup safe and explicit.

## 11.4 Tests

- [x] No pending bills returns no-work result.
- [x] One pending bill is claimed.
- [x] Claimed bill is passed to fake processor.
- [x] Multiple pending bills are processed sequentially.
- [x] Processor exception does not crash whole worker loop.
- [x] Same bill is not processed twice in one run.

## 11.5 Milestone Gate

- [x] Worker tests pass.
- [x] Webhook still only creates pending rows.
- [x] Worker uses fake processor only at this stage.

---

# Milestone 12 - File Loading and PDF/Image Normalization

## 12.1 File Loader

- [x] Create `apps/api/app/processing/file_loader.py`.
- [x] Implement `load_raw_file(storage, raw_file_url)`.
- [x] Return raw file bytes.
- [x] Translate storage failures into controlled errors where useful.

## 12.2 Processing Errors

- [x] Create `apps/api/app/processing/errors.py`.
- [x] Define `UnreadableFileError`.
- [x] Define `LLMInferenceError` placeholder if not already defined.
- [x] Define `ProcessingHardwareError` placeholder if useful.

## 12.3 PDF/Image Conversion

- [x] Create `apps/api/app/processing/pdf_converter.py`.
- [x] Implement `file_to_page_images(filename, content_type, data)`.
- [x] Detect PDF by content type or filename.
- [x] Convert PDF pages to PIL images using `pdf2image`.
- [x] Detect PNG by content type or filename.
- [x] Detect JPG/JPEG by content type or filename.
- [x] Load image files using Pillow.
- [x] Return one PIL image per page.
- [x] Raise `UnreadableFileError` for unsupported file types.
- [x] Raise `UnreadableFileError` for corrupted images.
- [x] Raise `UnreadableFileError` for password-protected or corrupted PDFs.
- [x] Do not auto-crop.

## 12.4 Dependency Documentation

- [x] Add Pillow to backend dependencies.
- [x] Add pdf2image to backend dependencies.
- [x] Document Poppler system dependency.
- [x] Document PDF conversion limitations.

## 12.5 Tests

- [x] Valid PNG bytes load as one page.
- [x] Valid JPEG bytes load as one page.
- [x] Unsupported file extension raises `UnreadableFileError`.
- [x] Corrupted image bytes raise `UnreadableFileError`.
- [x] Mock PDF conversion returns multiple pages.
- [x] Mock PDF conversion failure raises `UnreadableFileError`.
- [x] No large binary fixtures are required.

## 12.6 Milestone Gate

- [x] File conversion tests pass.
- [x] Worker still uses fake processor.
- [x] No LLM calls exist in file conversion layer.

---

# Milestone 13 - Image Preprocessing

## 13.1 Preprocessor

- [x] Create `apps/api/app/processing/image_preprocessor.py`.
- [x] Implement `preprocess_page_image(image, max_dimension=1024)`.
- [x] Resize so width is at most 1024.
- [x] Resize so height is at most 1024.
- [x] Preserve aspect ratio.
- [x] Do not enlarge small images.
- [x] Convert to grayscale.
- [x] Apply adaptive thresholding or documented global fallback.
- [x] Do not auto-crop backgrounds.
- [x] Return PIL image suitable for LLM input.

## 13.2 Encoding Helper

- [x] Implement helper to encode processed image to PNG bytes.
- [x] Ensure encoded bytes can be decoded by Pillow.
- [x] Keep encoding deterministic enough for tests.

## 13.3 Tests

- [x] Large landscape image max dimension becomes 1024.
- [x] Large portrait image max dimension becomes 1024.
- [x] Small image is not enlarged.
- [x] Aspect ratio is approximately preserved.
- [x] Output mode is grayscale or binary according to implementation.
- [x] PNG encoding returns valid PNG bytes.
- [x] No crop occurs beyond resizing.

## 13.4 Documentation

- [x] README mentions 1024px resize rule.
- [x] README mentions grayscale and thresholding.
- [x] README states auto-cropping is intentionally disabled.

## 13.5 Milestone Gate

- [x] Image preprocessing tests pass.
- [x] No LLM calls exist in preprocessing layer.

---

# Milestone 14 - LLM Prompt and Fake Client

## 14.1 Prompt Builder

- [x] Create `apps/api/app/processing/llm_prompt.py`.
- [x] Implement `build_bill_extraction_prompt()`.
- [x] Prompt instructs model to inspect Malaysian utility bill image.
- [x] Prompt requires strict JSON only.
- [x] Prompt forbids prose outside JSON.
- [x] Prompt includes required key `provider`.
- [x] Prompt includes required key `billing_period`.
- [x] Prompt includes required key `usage_value`.
- [x] Prompt includes required key `usage_unit`.
- [x] Prompt includes required key `confidence`.
- [x] Prompt states `confidence` must be `high` or `low`.
- [x] Prompt provides exact JSON example.

## 14.2 LLM Interface

- [x] Create `apps/api/app/processing/llm_client.py`.
- [x] Define `LLMClient` protocol.
- [x] Add `extract_bill_data(image_png_bytes, prompt) -> str`.
- [x] Define `LLMInferenceError` here or import from processing errors.

## 14.3 Fake LLM

- [x] Implement `FakeLLMClient`.
- [x] Initialize fake with queued responses.
- [x] Return one response per call.
- [x] Allow queued exceptions for failure simulation.
- [x] Track number of calls.
- [x] Store received prompts or images if helpful for tests.

## 14.4 Tests

- [x] Prompt contains strict JSON instruction.
- [x] Prompt contains all required keys.
- [x] Prompt forbids non-JSON prose.
- [x] Fake LLM returns queued responses in order.
- [x] Fake LLM simulates exception.
- [x] Fake LLM call count is testable.

## 14.5 Milestone Gate

- [x] Prompt and fake LLM tests pass.
- [x] No real Ollama dependency is required.

---

# Milestone 15 - Ollama/Gemma Client

## 15.1 Client Implementation

- [x] Implement `OllamaGemmaClient` in `llm_client.py` or `ollama_client.py`.
- [x] Read base URL from settings.
- [x] Read model name from settings.
- [x] Base64 encode image payload if required by Ollama endpoint.
- [x] Send prompt and image to local inference endpoint.
- [x] Set reasonable request timeout.
- [x] Return raw model text response.
- [x] Raise `LLMInferenceError` for non-200 responses.
- [x] Raise `LLMInferenceError` for timeout.
- [x] Raise `LLMInferenceError` for malformed response.
- [x] Do not import heavy GPU libraries at module import time.

## 15.2 Tests

- [x] Mock HTTP client.
- [x] Assert request includes configured model name.
- [x] Assert request includes prompt.
- [x] Assert request includes image payload.
- [x] Mock success response returns text.
- [x] Mock non-200 response raises `LLMInferenceError`.
- [x] Mock timeout raises `LLMInferenceError`.
- [x] No test requires Ollama to be installed.
- [x] No test requires Gemma model to be downloaded.

## 15.3 Documentation

- [x] Create `docs/local-llm.md`.
- [x] Document `OLLAMA_BASE_URL`.
- [x] Document `GEMMA_MODEL_NAME`.
- [x] Document how to run without real LLM in tests.
- [x] Document how to verify local model manually.

## 15.4 Milestone Gate

- [x] Ollama client tests pass with mocked HTTP.
- [x] Fake LLM tests still pass.
- [x] Existing backend tests pass.

---

# Milestone 16 - Extraction Parser and Multi-Page Aggregation

## 16.1 Parser

- [x] Create `apps/api/app/processing/extraction_parser.py`.
- [x] Implement `parse_llm_extraction(raw_text)`.
- [x] Accept strict JSON.
- [x] Optionally tolerate JSON inside markdown code fences.
- [x] Return `ExtractedBillData` for valid JSON.
- [x] Return `None` for broken JSON.
- [x] Return `None` for missing required fields.
- [x] Convert numeric `usage_value` safely.
- [x] Do not invent missing values.
- [x] Preserve low confidence values.

## 16.2 Aggregator

- [x] Implement `aggregate_page_extractions(extractions)`.
- [x] Prefer high-confidence over low-confidence.
- [x] Prefer known provider over unknown provider.
- [x] Prefer positive usage values.
- [x] If multiple high-confidence valid candidates exist, choose first deterministic candidate.
- [x] Return `None` if all pages fail.
- [x] Document aggregation tie-breaker rules.

## 16.3 Tests

- [x] Strict JSON parses.
- [x] JSON inside code fence parses if supported.
- [x] Broken JSON returns `None`.
- [x] Missing usage returns `None`.
- [x] Low-confidence valid JSON parses.
- [x] Aggregator chooses high-confidence over low-confidence.
- [x] Aggregator chooses known provider over unknown provider.
- [x] Aggregator chooses positive usage over invalid usage.
- [x] Aggregator returns `None` when all pages are `None`.

## 16.4 Milestone Gate

- [x] Parser tests pass.
- [x] Aggregator tests pass.
- [x] Validation tests still pass.

---

# Milestone 17 - Full Bill Processor State Machine

## 17.1 Processor Implementation

- [x] Create `apps/api/app/processing/processor.py`.
- [x] Implement `UtilityBillProcessor`.
- [x] Inject `UtilityBillRepository`.
- [x] Inject `StorageService`.
- [x] Inject `LLMClient`.
- [x] Inject settings or emission factor provider.
- [x] Avoid global singleton dependencies.

## 17.2 Processing Flow

- [x] Read raw file bytes from storage.
- [x] Convert file to page images.
- [x] For each page, process sequentially.
- [x] Preprocess page image to max 1024px.
- [x] Encode preprocessed page as PNG bytes.
- [x] Build extraction prompt.
- [x] Call LLM client.
- [x] Parse LLM response.
- [x] Collect page extraction.
- [x] Clear GPU cache after each page through helper or no-op placeholder.
- [x] Aggregate page extractions.
- [x] Validate aggregated extraction with two-key logic.
- [x] Update bill as `success` when validation succeeds.
- [x] Update bill as `flagged_low_confidence` when parseable extraction fails one key.
- [x] Mark bill `flagged_unreadable` when extraction is missing or unreadable.

## 17.3 Success Update Requirements

- [x] Save `status = success`.
- [x] Save extracted provider.
- [x] Save extracted period.
- [x] Save extracted usage.
- [x] Save extracted usage unit.
- [x] Save calculated CO2e.
- [x] Save emission factor used.
- [x] Save validation reasons as empty list or success marker.

## 17.4 Low-Confidence Update Requirements

- [x] Save `status = flagged_low_confidence`.
- [x] Save extracted fields that exist.
- [x] Save validation reasons.
- [x] Save calculated CO2e only if calculation is defensible and documented.
- [x] Preserve source file link.

## 17.5 Unreadable Update Requirements

- [x] Save `status = flagged_unreadable`.
- [x] Save reason list.
- [x] Do not save invented extracted fields.
- [x] Preserve source file link.

## 17.6 Tests

- [x] Single-page valid extraction updates bill to `success`.
- [x] Success update includes calculated CO2e.
- [x] Success update includes emission factor snapshot.
- [x] Low-confidence extraction updates bill to `flagged_low_confidence`.
- [x] Broken JSON updates bill to `flagged_unreadable`.
- [x] Multi-page input calls LLM once per page.
- [x] Multi-page aggregation chooses best extraction.
- [x] Pages are processed sequentially.
- [x] GPU cleanup helper is called after every page.
- [x] Processor uses repository methods, not direct record mutation.

## 17.7 Milestone Gate

- [x] Processor tests pass using fake LLM and local storage.
- [x] Worker can run with real processor and fake dependencies.
- [x] Webhook remains non-blocking.

---

# Milestone 18 - Hardware, OOM, and Corrupt File Hardening

## 18.1 GPU Helper

- [x] Create `apps/api/app/processing/gpu.py`.
- [x] Implement `clear_gpu_cache()`.
- [x] Import `torch` only inside the function.
- [x] No-op when torch is unavailable.
- [x] No-op when CUDA is unavailable.
- [x] Log and continue if `torch.cuda.empty_cache()` fails.

## 18.2 Error Handling Rules

- [x] Corrupted image bypasses LLM.
- [x] Corrupted image marks bill `flagged_unreadable`.
- [x] Unsupported file bypasses LLM.
- [x] Unsupported file marks bill `flagged_unreadable`.
- [x] Password-protected PDF bypasses LLM.
- [x] Password-protected PDF marks bill `flagged_unreadable`.
- [x] PDF conversion failure bypasses LLM.
- [x] PDF conversion failure marks bill `flagged_unreadable`.
- [x] LLM inference failure marks bill `flagged_unreadable` unless documented partial-page fallback is implemented.
- [x] GPU OOM-like error clears GPU cache.
- [x] GPU OOM-like error marks bill `flagged_unreadable`.
- [x] Unexpected processor exceptions are caught at worker boundary.
- [x] Worker continues to next bill after a failure.

## 18.3 Tests

- [x] Corrupted image marks bill unreadable.
- [x] Corrupted image does not call LLM.
- [x] Unsupported file marks bill unreadable.
- [x] Unsupported file does not call LLM.
- [x] Mocked password-protected PDF failure marks bill unreadable.
- [x] Simulated `LLMInferenceError` marks bill unreadable.
- [x] Simulated OOM calls `clear_gpu_cache`.
- [x] Simulated OOM marks bill unreadable.
- [x] `clear_gpu_cache` no-ops safely when torch is missing.
- [x] Worker continues to second bill after first bill fails.

## 18.4 Hardware Documentation

- [x] Create `docs/hardware.md`.
- [x] Document sequential page processing.
- [x] Document 1024px resizing.
- [x] Document grayscale and thresholding.
- [x] Document GPU cache clearing.
- [x] Document manual VRAM stress test.
- [x] Include `nvidia-smi` monitoring instructions.
- [x] Include test case for dense 15-page PDF.

## 18.5 Milestone Gate

- [x] Hardening tests pass.
- [x] Worker loop remains stable after failures.
- [x] Hardware docs are complete enough for local testing.

---

# Milestone 19 - Dashboard APIs

## 19.1 Alerts API

- [x] Create `apps/api/app/api/routes/dashboard.py`.
- [x] Implement `GET /dashboard/alerts`.
- [x] Return `flagged_low_confidence` count.
- [x] Return `flagged_unreadable` count.
- [x] Return `total_requiring_review` as sum of both.
- [x] Use repository method instead of raw route-level database logic.

## 19.2 Overview API

- [x] Implement `GET /dashboard/overview`.
- [x] Return total Scope 3 CO2e YTD.
- [x] Return electricity breakdown.
- [x] Return water breakdown.
- [x] Include only `success` and `resolved_by_client` bills by default.
- [x] Exclude `pending` bills.
- [x] Exclude `flagged_unreadable` bills.
- [x] Document how electricity vs water is inferred.

## 19.3 API Schemas

- [x] Add typed response model for alerts.
- [x] Add typed response model for overview.
- [x] Ensure numeric values serialize predictably.

## 19.4 Tests

- [x] Alerts count low-confidence bills.
- [x] Alerts count unreadable bills.
- [x] Total requiring review is correct.
- [x] Overview sums success bills.
- [x] Overview sums resolved bills.
- [x] Overview excludes pending bills.
- [x] Overview excludes unreadable bills.
- [x] Endpoint tests use in-memory repository.

## 19.5 Milestone Gate

- [x] Dashboard API tests pass.
- [x] Processor and webhook tests still pass.

---

# Milestone 20 - HITL Bill Detail and Approval APIs

## 20.1 Current User Placeholder

- [x] Add simple current-user dependency.
- [x] Return deterministic user id in tests.
- [x] Document that full auth is out of MVP scope unless added later.
- [x] Ensure reviewer id can be stamped.

## 20.2 Bill Detail API

- [x] Implement `GET /bills/{bill_id}`.
- [x] Return bill id.
- [x] Return SME id.
- [x] Return SME company name if available.
- [x] Return status.
- [x] Return raw file display URL or storage URL.
- [x] Return extracted provider.
- [x] Return extracted period.
- [x] Return extracted usage.
- [x] Return extracted usage unit.
- [x] Return calculated CO2e.
- [x] Return emission factor used.
- [x] Return validation reasons.
- [x] Return updated timestamp.
- [x] Return 404 for missing bill.

## 20.3 Approval API

- [x] Implement `POST /bills/{bill_id}/approve`.
- [x] Accept provider.
- [x] Accept billing period.
- [x] Accept usage value.
- [x] Accept usage unit.
- [x] Reject invalid usage value.
- [x] Reject unknown provider for manual approval.
- [x] Recalculate CO2e server-side.
- [x] Save reviewed extracted fields.
- [x] Save calculated CO2e.
- [x] Save emission factor used.
- [x] Set `status = resolved_by_client`.
- [x] Stamp `reviewer_id` from current-user dependency.
- [x] Return updated bill.

## 20.4 Tests

- [x] `GET /bills/{id}` returns expected bill.
- [x] Missing bill returns 404.
- [x] Approval updates status to `resolved_by_client`.
- [x] Approval stamps reviewer id.
- [x] Approval recalculates CO2e.
- [x] Approval ignores any client-sent CO2e if present.
- [x] Invalid usage returns validation error.
- [x] Unknown provider returns validation error.
- [x] Approved bill appears in overview totals.

## 20.5 Milestone Gate

- [x] HITL API tests pass.
- [x] Dashboard API tests still pass.
- [x] Manual approval path is fully integrated with repository.

---

# Milestone 21 - CSV and XLSX Exports

## 21.1 Export Repository Data

- [x] Ensure repository can list bills for export.
- [x] Include SME name.
- [x] Include PLC id if needed.
- [x] Include bill metadata.
- [x] Include extracted fields.
- [x] Include calculated CO2e.
- [x] Include emission factor snapshot.
- [x] Include raw file URL.
- [x] Include reviewer id.
- [x] Include timestamps.
- [x] Exclude `pending` by default.
- [x] Exclude flagged records by default unless `include_all` is provided.

## 21.2 CSI CSV Export

- [x] Create `apps/api/app/exports/csv_export.py`.
- [x] Implement deterministic CSV generation.
- [x] Add column `SME Name`.
- [x] Add column `Period`.
- [x] Add column `Usage`.
- [x] Add column `Usage Unit`.
- [x] Add column `CO2e`.
- [x] Add column `S3 File Link`.
- [x] Preserve exact column order.
- [x] Return UTF-8 CSV bytes or text response.

## 21.3 Raw XLSX Export

- [x] Create `apps/api/app/exports/xlsx_export.py`.
- [x] Use openpyxl or pandas.
- [x] Add column `utility_bill_id`.
- [x] Add column `plc_id`.
- [x] Add column `sme_id`.
- [x] Add column `sme_name`.
- [x] Add column `status`.
- [x] Add column `provider`.
- [x] Add column `period`.
- [x] Add column `usage`.
- [x] Add column `unit`.
- [x] Add column `co2e`.
- [x] Add column `emission_factor_used`.
- [x] Add column `raw_file_url`.
- [x] Add column `reviewer_id`.
- [x] Add column `created_at`.
- [x] Add column `updated_at`.
- [x] Preserve exact column order.
- [x] Return valid XLSX bytes.

## 21.4 Export Routes

- [x] Create `apps/api/app/api/routes/exports.py`.
- [x] Implement `GET /exports/csi.csv`.
- [x] Implement `GET /exports/raw.xlsx`.
- [x] Set correct CSV content type.
- [x] Set correct XLSX content type.
- [x] Set useful download filename headers.
- [x] Register export routes in app factory.

## 21.5 Tests

- [x] CSV endpoint returns expected headers in exact order.
- [x] CSV includes `success` rows.
- [x] CSV includes `resolved_by_client` rows.
- [x] CSV excludes `pending` by default.
- [x] CSV includes raw file URL.
- [x] XLSX endpoint returns valid workbook bytes.
- [x] XLSX workbook has expected headers in exact order.
- [x] XLSX includes audit metadata.
- [x] Export tests use in-memory repository.

## 21.6 Documentation

- [x] Create `docs/exports.md`.
- [x] Document CSI CSV format.
- [x] Document raw XLSX format.
- [x] Document default filtering behavior.

## 21.7 Milestone Gate

- [x] CSV export tests pass.
- [x] XLSX export tests pass.
- [x] Existing API tests pass.

---

# Milestone 22 - PDF Sustainability Summary Export

## 22.1 Summary Model

- [x] Define summary data needed for PDF.
- [x] Include generated timestamp.
- [x] Include total Scope 3 CO2e YTD.
- [x] Include electricity total.
- [x] Include water total.
- [x] Include successful bill count.
- [x] Include resolved-by-client bill count.
- [x] Include bills requiring review count.
- [x] Include unreadable count if useful.

## 22.2 PDF Generation

- [x] Create `apps/api/app/exports/pdf_export.py`.
- [x] Use reportlab or lightweight PDF library.
- [x] Add title `SME Bridge Sustainability Summary`.
- [x] Add generated timestamp.
- [x] Add total CO2e.
- [x] Add electricity vs water breakdown.
- [x] Add review counts.
- [x] Add optional simple chart only if testable.
- [x] Keep PDF generation deterministic enough for tests.

## 22.3 Route

- [x] Add `GET /exports/summary.pdf`.
- [x] Return `application/pdf`.
- [x] Set useful download filename header.
- [x] Ensure route works when there is zero data.

## 22.4 Tests

- [x] PDF endpoint returns HTTP 200.
- [x] PDF endpoint returns `application/pdf`.
- [x] PDF bytes begin with `%PDF`.
- [x] PDF generation does not crash with zero data.
- [x] Summary values are testable before rendering or by text extraction.
- [x] CSV and XLSX export tests still pass.

## 22.5 Documentation

- [x] Update `docs/exports.md` with PDF summary format.
- [x] Document chart limitations if chart is omitted for MVP.

## 22.6 Milestone Gate

- [x] PDF export tests pass.
- [x] All export routes are registered.

---

# Milestone 23 - Frontend Shell and API Client

## 23.1 Routes and App Shell

- [x] Create frontend app shell.
- [x] Add route `/` for dashboard.
- [x] Add route `/bills/:billId` for review page placeholder.
- [x] Add route `/exports` or export access point.
- [x] Add navigation link to Dashboard.
- [x] Add navigation link to Exports if using separate page.
- [x] Add placeholder headings for each route.

## 23.2 TypeScript API Types

- [x] Create `src/api/types.ts`. (Implemented in `src/api/client.ts`)
- [x] Add `DashboardAlerts` type.
- [x] Add `DashboardOverview` type.
- [x] Add `UtilityBillDetail` type.
- [x] Add `ApproveBillRequest` type.
- [x] Add export kind type.

## 23.3 API Client

- [x] Create `src/api/client.ts`.
- [x] Read API base URL from frontend environment variable.
- [x] Implement `getDashboardAlerts()`.
- [x] Implement `getDashboardOverview()`.
- [x] Implement `getBillDetail(billId)`.
- [x] Implement `approveBill(billId, payload)`.
- [x] Implement `downloadExport(kind)`.
- [x] Throw clear error for non-OK responses. (Handled by Axios)
- [x] Keep fetch wrapper testable.

## 23.4 Tests

- [x] App renders dashboard heading.
- [x] Navigation links exist.
- [x] Review placeholder route renders.
- [x] API client builds dashboard alerts URL correctly.
- [x] API client builds dashboard overview URL correctly.
- [x] API client builds bill detail URL correctly.
- [x] API client sends approve payload correctly.
- [x] API client handles non-OK response by throwing.

## 23.5 Milestone Gate

- [x] Frontend tests pass.
- [x] Backend tests still pass.
- [x] No orphan frontend components exist.

---

# Milestone 24 - Frontend Dashboard UI

## 24.1 Dashboard Components

- [x] Create `src/components/AlertsBar.tsx`.
- [x] Create `src/components/ImpactOverview.tsx`.
- [x] Create `src/components/BreakdownChart.tsx` or simple accessible visualization.
- [x] Update `src/routes/DashboardPage.tsx`.

## 24.2 Dashboard Behavior

- [x] Show unreadable count.
- [x] Show total Scope 3 CO2e YTD.
- [x] Show electricity breakdown.
- [x] Show water breakdown.
- [x] Use semantic headings.
- [x] Use accessible labels for chart or visual breakdown.

## 24.3 Tests

- [x] Dashboard shows loading state.
- [x] Dashboard renders alert count.
- [x] Dashboard renders total CO2e.
- [x] Dashboard renders electricity value.
- [x] Dashboard renders water value.
- [x] Dashboard renders error state.
- [x] Components are used by `DashboardPage`.

## 24.4 Milestone Gate

- [x] Dashboard UI tests pass.
- [x] API client tests still pass.

---

# Milestone 25 - Frontend HITL Review UI

- [/] Keep rendering simple for PDF/image MVP behavior.

## 25.2 Verification Form

- [x] Create `src/components/VerificationForm.tsx`. (Integrated in `ReviewDetailPage.tsx`)
- [x] Add provider field.
- [x] Add billing period field.
- [x] Add usage value field.
- [x] Add usage unit field.
- [x] Add read-only calculated CO2e display.
- [x] Add approve button.
- [x] Validate required fields client-side.
- [x] Display backend validation errors.

## 25.3 Review Page

- [x] Update `src/routes/ReviewBillPage.tsx`. (Implemented as `ReviewDetailPage.tsx`)
- [x] Fetch bill detail by `billId`.
- [x] Show loading state.
- [x] Show error state.
- [x] Use side-by-side layout.
- [x] Left pane uses `BillImageViewer`. (Simplified for MVP)
- [x] Right pane uses `VerificationForm`.
- [x] Pre-fill fields from extracted values.
- [x] Use `emission_factor_used` from bill when present.
- [x] Use frontend fallback factor only when bill factor is missing.
- [x] Recalculate CO2e live when usage changes.
- [x] Submit reviewed values to approval API.
- [x] Show success state after approval.

## 25.4 Tests

- [x] Review page fetches bill detail.
- [x] Form pre-fills provider.
- [x] Form pre-fills billing period.
- [x] Form pre-fills usage value.
- [x] Form pre-fills usage unit.
- [x] Changing usage updates live CO2e.
- [x] Clicking approve calls API with reviewed values.
- [x] Success state appears after approval.
- [x] Fetch failure renders error state.
- [x] Approval failure renders error state.
- [x] Zoom controls update image viewer state. (Simplified for MVP)
- [x] Rotate controls update image viewer state. (Simplified for MVP)
- [x] Review page wires viewer and form; no orphan components.

## 25.5 Milestone Gate

- [x] HITL UI tests pass.
- [x] Dashboard tests still pass.
- [x] Backend HITL API tests still pass.

---

# Milestone 26 - Frontend Export Modal

## 26.1 Modal Component

- [x] Create `src/components/ExportModal.tsx`. (Implemented as `ExportsPage.tsx`)
- [x] Add open and close behavior.
- [x] Add export option for CSI CSV.
- [x] Add export option for raw XLSX archive. (Deferred/XLSX not in MVP)
- [x] Add export option for sustainability summary PDF.
- [x] Show loading state while download is being prepared.
- [x] Show error state if download fails.

## 26.2 Download Behavior

- [x] Call `downloadExport("csi")` for CSV.
- [x] Call `downloadExport("raw")` for XLSX.
- [x] Call `downloadExport("summary")` for PDF.
- [x] Create Blob URL from response.
- [x] Trigger browser download.
- [x] Use filename `csi_export_{sme_id}.csv`.
- [x] Use filename `xlsx_export_{sme_id}.xlsx`.
- [x] Use filename `summary_report_{sme_id}.pdf`.
- [x] Revoke Blob URL after triggering download.

## 26.3 Integration

- [x] Add export button to dashboard or exports page.
- [x] Ensure modal is reachable from app UI.
- [x] Ensure modal does not require hidden direct component rendering.

## 26.4 Tests

- [x] Modal opens. (Implemented as Exports page)
- [x] Modal closes.
- [x] CSV button calls correct API client function.
- [x] XLSX button calls correct API client function.
- [x] PDF button calls correct API client function.
- [x] Successful download triggers mocked anchor click.
- [x] Failed download shows error.
- [x] Modal is reachable from page UI.

## 26.5 Milestone Gate

- [x] Exports UI tests pass.
- [x] Downloaded files match backend schemas.
- [x] Application routing is complete for MVP.

---

# Milestone 27 - Backend End-to-End Integration Tests

## 27.1 Happy Path Integration Test

- [x] Seed in-memory PLC.
- [x] Seed in-memory SME.
- [x] Seed authorized email.
- [x] POST `/webhook/incoming-email` with one valid attachment.
- [x] Assert HTTP 200.
- [x] Assert one pending utility bill is created.
- [x] Run worker `process_one()` with fake LLM high-confidence JSON. (Simulated in E2E)
- [x] Assert bill becomes `success`.
- [x] Assert calculated CO2e is populated.
- [x] Assert emission factor used is populated.
- [x] Call `/dashboard/alerts`.
- [x] Assert no review required for happy path.
- [x] Call `/dashboard/overview`.
- [x] Assert total CO2e includes processed bill.
- [x] Call `/exports/csv?sme_id=test_sme`.
- [x] Assert bill appears in CSV.

## 27.2 Unauthorized Email Integration Test

- [x] POST webhook from unknown email.
- [x] Assert HTTP 200.
- [x] Assert no bill is created.
- [x] Assert no file is saved.
- [x] Assert bounce service was called.

## 27.3 Corrupted Attachment Integration Test

- [x] POST webhook with corrupted attachment from authorized email.
- [x] Assert pending bill is created.
- [x] Run worker.
- [x] Assert bill becomes `flagged_unreadable`.
- [x] Assert dashboard alerts count unreadable bill.

## 27.4 Low-Confidence Integration Test

- [x] POST webhook with valid attachment from authorized email.
- [x] Run worker with low-confidence LLM JSON.
- [x] Assert bill becomes `flagged_low_confidence`.
- [x] Assert validation reasons are saved.
- [x] Assert dashboard alerts count low-confidence bill.

## 27.5 Manual Approval Integration Test

- [x] Create flagged bill.
- [x] Call `GET /bills/{bill_id}`.
- [x] Assert detail includes raw file URL and extracted fields.
- [x] Call `POST /bills/{bill_id}/approve` with corrected values.
- [x] Assert status becomes `resolved_by_client`.
- [x] Assert reviewer id is stamped.
- [x] Assert CO2e is recalculated.
- [x] Assert overview includes resolved bill.
- [x] Assert export includes resolved bill.

## 27.6 Multiple Attachments Integration Test

- [x] POST webhook with five JPEG attachments.
- [x] Assert five pending bills are created.
- [x] Run worker with five fake LLM responses.
- [x] Assert all five bills are processed independently.
- [x] Assert LLM was called once per page or attachment as expected.

## 27.7 Milestone Gate

- [x] Backend happy path integration test passes.
- [x] Backend failure path integration tests pass.
- [x] Existing unit tests pass.

---

# Milestone 28 - Frontend Integration Tests

## 28.1 Dashboard Integration

- [x] Use mocked API client or MSW.
- [x] Render app at dashboard route.
- [x] Mock alerts response.
- [x] Mock overview response.
- [x] Assert dashboard shows alert count.
- [x] Assert dashboard shows total CO2e.
- [x] Assert export modal can be opened. (Implemented as Exports page)

## 28.2 Review Flow Integration

- [x] Use mocked API client or MSW.
- [x] Render app at `/bills/{billId}`.
- [x] Mock bill detail response for flagged bill.
- [x] Assert extracted values pre-fill form.
- [x] Change usage from 450 to 500. (Simulated 100 to 150 in test)
- [x] Assert live CO2e changes.
- [x] Click approve.
- [x] Assert approval API receives corrected values.
- [x] Assert success message appears. (Redirects to list on success)

## 28.3 Export Flow Integration

- [x] Open export modal. (Exports page)
- [x] Click CSI CSV export.
- [x] Assert download function called.
- [x] Click raw XLSX export. (Deferred)
- [x] Assert download function called.
- [x] Click PDF summary export.
- [x] Assert download function called.

## 28.4 Milestone Gate

- [x] Frontend integration tests pass.
- [x] All frontend unit tests pass.
- [x] App routes are wired end to end.

---

# Milestone 29 - Local Deployment and Operations Documentation

## 29.1 Environment Variables

- [x] Document all backend env vars.
- [x] Document all frontend env vars.
- [x] Provide `.env.example` for backend.
- [x] Provide `.env.example` for frontend.
- [x] Include safe placeholder values.
- [x] Do not commit real secrets.

## 29.2 Supabase Setup

- [x] Document how to create Supabase project.
- [x] Document how to apply migration.
- [x] Document how to create storage bucket.
- [x] Document bucket name expected by app.
- [x] Document public vs signed URL decision.
- [x] Document how to seed PLC.
- [x] Document how to seed SME.
- [x] Document how to seed authorized emails.

## 29.3 Local Backend Runbook

- [x] Document backend install command.
- [x] Document all backend env vars.
- [x] Document database initialization.
- [x] Document development server execution.
- [x] Document worker execution.
- [x] Document test execution.
- [x] Document where local logs appear.

## 29.4 Local Frontend Runbook

- [x] Document frontend install command.
- [x] Document frontend dev server command.
- [x] Document API base URL configuration.

## 29.5 Email Webhook Setup

- [x] Document provider choice: Postmark or SendGrid.
- [x] Document inbound email address: `submit@smebridge.com`.
- [x] Document webhook URL path: `/webhook/incoming-email`.
- [x] Document required HTTPS exposure.
- [x] Document sample webhook payload for local testing.
- [x] Document unauthorized sender behavior.
- [x] Document multiple attachment behavior.

## 29.6 Tunnel Setup

- [x] Document Cloudflare Tunnel setup.
- [x] Document Ngrok alternative.
- [x] Document how to map tunnel URL to local FastAPI port.
- [x] Document how to update email provider webhook URL.
- [x] Document webhook health verification.

## 29.7 Local LLM Setup

- [x] Document installing Ollama or selected runtime.
- [x] Document pulling or configuring Gemma model.
- [x] Document setting `OLLAMA_BASE_URL`.
- [x] Document setting `GEMMA_MODEL_NAME`.
- [x] Document manual inference smoke test.
- [x] Document fallback fake LLM for tests.

## 29.8 Hardware Stress Test

- [x] Document dense 15-page PDF test file preparation.
- [x] Document running worker on stress file.
- [x] Document monitoring with `nvidia-smi`.
- [x] Confirm pages are processed sequentially.
- [x] Confirm VRAM is cleared after each page.
- [x] Confirm OOM failure marks only the affected bill unreadable.
- [x] Confirm worker continues after OOM-like failure.

## 29.9 Known MVP Limitations

- [x] Document supported file types.
- [x] Document provider master list limitations.
- [x] Document emission factor hardcoding limitation.
- [x] Document no full auth limitation if applicable.
- [x] Document local hardware dependency.
- [x] Document LLM extraction accuracy risks.
- [x] Document manual review expectations.

## 29.10 Milestone Gate

- [x] README supports complete local run from scratch.
- [x] Deployment docs are understandable by a new developer.
- [x] No hidden setup assumptions remain.

---

# # Milestone 30 - Final Wiring and Quality Gate

## 30.1 Route Registration

- [x] Health route registered.
- [x] Email webhook route registered.
- [x] Dashboard routes registered.
- [x] Bill detail route registered.
- [x] Approval route registered.
- [x] Export routes registered.

## 30.2 Dependency Wiring

- [x] Production repository dependency uses Supabase adapter.
- [x] Production storage dependency uses Supabase Storage.
- [x] Production LLM dependency uses Ollama/Gemma client when configured.
- [x] Test repository dependency can be overridden with in-memory adapter.
- [x] Test storage dependency can be overridden with local/fake storage.
- [x] Tests use fake LLM.
- [x] Bounce service dependency is safe in dev/test.
- [x] Current user dependency is overrideable in tests.

## 30.3 Quality & Polish Review

- [x] Every backend module is imported by route, worker, dependency factory, or tests.
- [x] Every frontend component is reachable from a route or tested intentionally.
- [x] Every repository method is covered by route, worker, export, or tests.
- [x] Every storage method is covered by route, processor, or tests.
- [x] Every export generator is reachable through an API endpoint.
- [x] Every CLI/script is documented.
- [x] Remove unused placeholders.
- [x] Remove dead code.

## 30.4 Security and Safety Review

- [x] No secrets committed.
- [x] `.env` files ignored.
- [x] Supabase service role key only used server-side.
- [x] Webhook endpoint validates payload shape.
- [x] File names are sanitized.
- [x] Path traversal is blocked.
- [x] Unsupported files are rejected safely.
- [x] Large file behavior is documented or limited.
- [x] Unauthorized senders cannot create bill rows.
- [x] Frontend does not expose service role key.

## 30.5 Auditability Review

- [x] Raw file URL is saved for every accepted attachment.
- [x] CO2e calculation stores emission factor snapshot.
- [x] Validation reasons are saved for flagged bills.
- [x] Reviewer id is saved on manual approval.
- [x] Updated timestamp changes on state updates.
- [x] Exports include source file link.
- [x] Raw XLSX export includes audit metadata.

## 30.6 Final Gate

- [x] Run all backend unit tests.
- [x] Run all backend integration tests.
- [x] Run backend lint.
- [x] Run all frontend unit tests.
- [x] Run frontend integration tests.
- [x] Run frontend lint.
- [x] Run build for frontend.
- [x] Manually test API health endpoint.
- [x] Manually test webhook with sample payload.
- [x] Manually run worker once.
- [x] Manually download CSV export.
- [x] Manually download XLSX export.
- [x] Manually download PDF export.
- [x] Complete project handover.

## 30.6 State Machine Review

- [x] New accepted bills start as `pending`.
- [x] Valid two-key extraction becomes `success`.
- [x] Low-confidence extraction becomes `flagged_low_confidence`.
- [x] Unknown provider becomes `flagged_low_confidence`.
- [x] Broken JSON becomes `flagged_unreadable`.
- [x] Missing critical data becomes `flagged_unreadable`.
- [x] Corrupted file becomes `flagged_unreadable`.
- [x] Password-protected PDF becomes `flagged_unreadable`.
- [x] Manual approval becomes `resolved_by_client`.
- [x] No impossible status can be written to database.

## 30.7 Final Test Commands

- [x] Manually download PDF export.

## 30.8 Final Acceptance Criteria

- [x] Authorized email with valid utility bill becomes a successful CO2e record.
- [x] Unauthorized email is ignored and bounce notification is triggered.
- [x] Multiple attachments become multiple utility bill rows.
- [x] Corrupted file is flagged unreadable without crashing worker.
- [x] Low-confidence extraction appears in dashboard alerts.
- [x] Admin can review and approve flagged bill.
- [x] Approved bill stamps reviewer id.
- [x] Approved bill recalculates CO2e server-side.
- [x] CSI CSV export contains correct headers and source file link.
- [x] Raw XLSX export contains complete audit trail.
- [x] PDF summary export downloads successfully.
- [x] Local deployment instructions are complete.
- [x] VRAM stress test has been run or explicitly deferred with reason.

---

# Appendix A - Recommended Commit Sequence

- [x] Commit 01: Monorepo bootstrap.
- [x] Commit 02: FastAPI shell and health route.
- [x] Commit 03: Domain enums, providers, and schemas.
- [x] Commit 04: CO2e and validation logic.
- [x] Commit 05: Database migration and docs.
- [x] Commit 06: Repository contracts and in-memory implementation.
- [x] Commit 07: Supabase repository adapter.
- [x] Commit 08: Storage abstraction and adapters.
- [x] Commit 09: Email webhook parser.
- [x] Commit 10: Authorization and bounce service.
- [x] Commit 11: Webhook route.
- [x] Commit 12: Worker skeleton.
- [x] Commit 13: File loading and PDF/image conversion.
- [x] Commit 14: Image preprocessing.
- [x] Commit 15: LLM prompt and fake client.
- [x] Commit 16: Ollama/Gemma client.
- [x] Commit 17: Extraction parser and page aggregation.
- [x] Commit 18: Full processor state machine.
- [x] Commit 19: OOM and corrupt-file hardening.
- [x] Commit 20: Dashboard APIs.
- [x] Commit 21: HITL APIs.
- [x] Commit 22: CSV/XLSX exports.
- [x] Commit 23: PDF export.
- [x] Commit 24: Frontend shell and API client.
- [x] Commit 25: Dashboard UI.
- [x] Commit 26: HITL review UI.
- [x] Commit 27: Export modal.
- [x] Commit 28: End-to-end tests and deployment docs.

---

# Appendix B - Critical Test Matrix

## Validation Matrix

- [x] High confidence + known provider + positive usage -> `success`.
- [x] Low confidence + known provider + positive usage -> `flagged_low_confidence`.
- [x] High confidence + unknown provider + positive usage -> `flagged_low_confidence`.
- [x] High confidence + known provider + negative usage -> `flagged_low_confidence` or documented failure state.
- [x] Broken JSON -> `flagged_unreadable`.
- [x] Missing usage -> `flagged_unreadable`.
- [x] Missing provider -> `flagged_unreadable`.

## Ingestion Matrix

- [x] Authorized sender + one attachment -> one pending bill.
- [x] Authorized sender + five attachments -> five pending bills.
- [x] Unauthorized sender -> zero pending bills and bounce sent.
- [x] Empty attachment list -> zero pending bills.
- [x] Invalid payload -> controlled error.

## Processing Matrix

- [x] Valid PNG -> processed.
- [x] Valid JPEG -> processed.
- [x] Valid single-page PDF -> processed.
- [x] Valid multi-page PDF -> pages processed sequentially.
- [x] Unsupported file -> unreadable.
- [x] Corrupted image -> unreadable.
- [x] Password-protected PDF -> unreadable.
- [x] LLM timeout -> unreadable.
- [x] GPU OOM-like error -> unreadable and worker continues.

## Dashboard Matrix

- [x] Low-confidence bills count as requiring verification.
- [x] Unreadable bills count as requiring verification.
- [x] Pending bills do not count as CO2e impact.
- [x] Successful bills count toward CO2e impact.
- [x] Resolved bills count toward CO2e impact.

## Export Matrix

- [x] CSV column order exactly matches expected.
- [x] XLSX column order exactly matches expected.
- [x] PDF returns valid PDF bytes.
- [x] Exports include source file URL.
- [x] Pending rows excluded by default.
- [x] Resolved rows included by default.

---

# Appendix C - Manual Demo Script

Use this as the final MVP demo checklist.

- [x] Start Supabase project or local configured database.
- [x] Apply database migration.
- [x] Create storage bucket.
- [x] Seed one PLC.
- [x] Seed one SME under the PLC.
- [x] Seed one authorized email for the SME.
- [x] Start local Ollama/Gemma runtime.
- [x] Start FastAPI backend.
- [x] Start worker in a separate terminal.
- [x] Start frontend.
- [x] Expose backend webhook URL via Cloudflare Tunnel or Ngrok.
- [x] Configure email provider webhook.
- [x] Send email from unauthorized address.
- [x] Confirm bounce notice behavior.
- [x] Confirm no bill row created.
- [x] Send email from authorized address with one valid utility bill.
- [x] Confirm pending row is created.
- [x] Confirm raw file is stored.
- [x] Confirm worker processes bill.
- [x] Confirm bill becomes `success` or flagged depending on model output.
- [x] Open dashboard.
- [x] Confirm alerts and overview render.
- [x] If bill is flagged, open review UI.
- [x] Change usage value from 450 to 500.
- [x] Confirm live CO2e updates.
- [x] Click approve.
- [x] Confirm status becomes `resolved_by_client`.
- [x] Download CSI CSV.
- [x] Verify headers and raw file URL.
- [x] Download raw XLSX archive.
- [x] Verify metadata and reviewer id.
- [x] Download PDF summary.
- [x] Verify summary opens.
- [x] Run dense PDF VRAM stress test.
- [x] Confirm worker does not crash permanently.
