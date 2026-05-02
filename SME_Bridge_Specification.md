Here is the comprehensive, developer-ready Technical Specification for the SME Bridge MVP. This document integrates all of our architectural decisions, adds the necessary database schemas and API routing structures, and includes the requested error-handling and testing protocols.

You can hand this directly to your development team at Gapura Studio.

***

# Technical Specification: SME Bridge (MVP Prototype)

## 1. Project Overview
**Objective:** A B2B SaaS platform for the Malaysian ESG sector that solves the Scope 3 data collection bottleneck. It allows SME suppliers to submit utility bills via a zero-friction email gateway. The system extracts "Audit-Ready" CO2e data, permanently linked to the source image, formatted for Bursa Malaysia's CSI platform.

**MVP Tech Stack & Environment:**
*   **Backend:** Python (FastAPI).
*   **Database & File Storage:** Supabase (PostgreSQL for relational data, S3 for raw/processed images).
*   **LLM Engine:** Google Gemma 4 (E4B variant) running locally via Ollama/HuggingFace.
*   **Deployment (Phase 1 Sandbox):** Hosted locally on Lenovo LOQ i5 (RTX 3060, 6GB VRAM). Network exposed securely via Cloudflare Tunnels (or Ngrok) for HTTPS webhook reception.

---

## 2. Database Schema (Supabase PostgreSQL)
The relational model revolves around linking SMEs to PLCs and tracking the state of utility submissions.

*   **`plcs` (Public Listed Companies)**
    *   `id` (UUID, Primary Key)
    *   `name` (String)
*   **`smes` (SME Suppliers)**
    *   `id` (UUID, Primary Key)
    *   `plc_id` (UUID, Foreign Key)
    *   `company_name` (String)
*   **`authorized_emails` (Whitelist)**
    *   `id` (UUID, Primary Key)
    *   `sme_id` (UUID, Foreign Key)
    *   `email_address` (String, Unique)
*   **`utility_bills` (Submissions & State)**
    *   `id` (UUID, Primary Key)
    *   `sme_id` (UUID, Foreign Key)
    *   `status` (Enum: `pending`, `success`, `flagged_low_confidence`, `flagged_unreadable`, `resolved_by_client`)
    *   `raw_file_url` (String - Supabase S3 link)
    *   `extracted_provider` (String)
    *   `extracted_period` (String/Date)
    *   `extracted_usage` (Integer)
    *   `calculated_co2e` (Float)
    *   `emission_factor_used` (Float - Hardcoded snapshot for audit)
    *   `reviewer_id` (UUID - Nullable, populated on HITL intervention)
    *   `updated_at` (Timestamp)

---

## 3. Data Ingestion & Pre-Processing Pipeline
### 3.1 The Email Gateway
*   **Endpoint:** A single Cloudflare Tunnel URL mapped to a FastAPI `POST /webhook/incoming-email` route.
*   **Provider:** Use a transactional email provider (e.g., Postmark, SendGrid) to route emails sent to `submit@smebridge.com` into JSON webhooks.
*   **Authentication Check:** 
    *   Extract the `From:` address.
    *   Query `authorized_emails`.
    *   *If Not Found:* Drop payload. Trigger automated transactional email bounce: *"Your email address is not recognized. Please contact your PLC sustainability team to authorize this address."*
    *   *If Found:* Save the raw attachment to Supabase S3. Create a new row in `utility_bills` with status `pending`.

### 3.2 Pre-Processing (GPU Protection Protocol)
To ensure the 6GB VRAM limit is strictly respected:
1.  **Queue System:** A background worker (e.g., Celery or FastAPI `BackgroundTasks`) picks up `pending` bills one at a time.
2.  **PDF Handling (`pdf2image`):** Convert multi-page PDFs to an array of images in memory.
3.  **Optimization:** Resize to max 1024px width/height. Apply grayscale and adaptive thresholding to boost ink contrast. *Crucial:* Do not auto-crop backgrounds.
4.  **Sequential Processing:** Feed Page 1 to Gemma. Clear VRAM. Feed Page 2 to Gemma. Clear VRAM. Aggregate valid JSON outputs.

---

## 4. Extraction & State Machine (Two-Key Validation)
### 4.1 LLM Prompt Instructions
The prompt to Gemma 4 E4B must enforce strict JSON output:
```json
{
  "provider": "TNB", 
  "billing_period": "YYYY-MM",
  "usage_value": 450,
  "usage_unit": "kWh",
  "confidence": "high" // or "low" based on legibility
}
```

### 4.2 State Machine Logic
FastAPI evaluates the aggregated JSON output against two keys to determine the final database state:
*   **Key 1 (Generative):** Did Gemma explicitly output `"confidence": "high"`?
*   **Key 2 (Deterministic Python Validation):**
    *   Is `usage_value` a valid, positive number?
    *   Is `provider` found in the master list of Malaysian utility companies (TNB, Air Selangor, etc.)?
*   **Routing:**
    *   If Key 1 AND Key 2 pass: Status = `success`. Calculate CO2e using hardcoded Malaysian Grid Emission Factors.
    *   If Key 1 OR Key 2 fails: Status = `flagged_low_confidence`.
    *   If JSON is broken/missing data: Status = `flagged_unreadable`.

---

## 5. Client Dashboard & HITL UI (Frontend)
### 5.1 Hybrid Dashboard Views
*   **Alerts Bar:** Passive pull notifications indicating bills that require review (e.g., "5 Bills Require Verification").
*   **Impact Overview:** Visuals displaying Total Scope 3 CO2e Tracked YTD and an Electricity vs. Water breakdown chart.
*   **HITL Verification UI (Side-by-Side):**
    *   **Left Pane:** Component to display, zoom, and rotate the raw utility bill image fetched from Supabase S3.
    *   **Right Pane:** Form pre-filled with Gemma's extracted data.
    *   **Live Math:** Editing the `usage_value` in the form instantly updates the `calculated_co2e` UI field based on the hardcoded Emission Factors.
    *   **Action:** Clicking "Approve" changes the database status to `resolved_by_client` and stamps the admin's `reviewer_id`.

### 5.2 Export Module
A modal that queries the `utility_bills` table and generates downloadable files via Python (`pandas`):
1.  **CSI Prescribed Format (.csv):** Strictly formatted for Bursa Malaysia (SME Name, Period, Usage, CO2e, S3 File Link).
2.  **Raw Data Archive (.xlsx):** Complete audit trail including metadata, timestamps, and reviewer IDs.
3.  **Sustainability Summary (.pdf):** High-level aggregate charts for management.

---

## 6. Error Handling & Edge Cases
*   **OOM (Out of Memory) GPU Crashes:** If the local Gemma inference crashes due to an unusually large image array, the Python `try/except` block must catch the hardware exception, clear the PyTorch/CUDA cache (`torch.cuda.empty_cache()`), mark the bill as `flagged_unreadable`, and continue to the next item in the queue.
*   **Email Webhook Timeouts:** Because the webhook provider expects a `200 OK` response quickly, the FastAPI endpoint must *only* handle file saving and DB row creation synchronously. LLM processing MUST be handled asynchronously to prevent the webhook provider from retrying the same email multiple times.
*   **Multiple Attachments:** If an SME attaches 5 separate JPEGs to one email, the system processes them as 5 distinct `utility_bills` rows.
*   **Corrupted Files/Password Protected PDFs:** If `pdf2image` fails to open a file, it bypasses the LLM entirely and immediately flags the database row as `flagged_unreadable`.

---

## 7. Testing Plan
### Phase 1: Unit Testing (Logic & Validation)
*   **Deterministic Validation Tests:** Feed mock JSON payloads (both perfect and intentionally malformed) into the FastAPI validation script to ensure the Two-Key logic accurately sorts items into `success`, `flagged_low_confidence`, and `flagged_unreadable`.
*   **CO2e Math Tests:** Assert that specific `usage_values` output the exact correct `calculated_co2e` based on the hardcoded Malaysian Emission Factors.

### Phase 2: Integration Testing (Pipeline & Hardware)
*   **The Ingestion Mock:** Send a mock JSON webhook payload simulating an email from a whitelisted address and assert that the file lands in S3 and a `pending` row is created. Send a payload from a non-whitelisted address and assert it is dropped.
*   **The VRAM Stress Test:** Feed a single, heavily dense, 15-page PDF into the processing queue. Monitor the RTX 3060 VRAM using `nvidia-smi` to ensure the sequential page-by-page processing successfully clears the cache and prevents OOM errors.

### Phase 3: User Acceptance Testing (Dashboard)
*   **HITL Verification Flow:** Log into the dashboard as a PLC Admin. Open a `flagged_low_confidence` bill. Change the usage value from "450" to "500". Verify that the Live Calculation updates instantly. Click "Approve" and verify the database registers `resolved_by_client` and stamps the correct `reviewer_id`.
*   **Export Verification:** Download the CSI format `.csv` and manually verify that the column headers and S3 URLs map correctly.