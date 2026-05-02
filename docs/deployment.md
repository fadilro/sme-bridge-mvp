# SME Bridge MVP Deployment Guide

This guide covers setting up the application for local development and testing, including the required external services.

## Environment Variables

### Backend (`apps/api/.env`)
- `SUPABASE_URL`: The URL for your Supabase project.
- `SUPABASE_SERVICE_ROLE_KEY`: The service role key for your Supabase project (do not use the anon key).
- `SUPABASE_STORAGE_BUCKET`: The name of the storage bucket for raw files (e.g., `utility-bills`).
- `OLLAMA_BASE_URL`: URL where Ollama is running (default: `http://localhost:11434`).
- `GEMMA_MODEL_NAME`: The model name to use for extraction (e.g., `gemma2`).
- `EMISSION_FACTOR_ELECTRICITY_KWH`: The carbon emission factor (e.g., `0.58`).

### Frontend (`apps/web/.env`)
- `VITE_API_URL`: The URL of your local backend API (default: `http://localhost:8000`).

## Supabase Setup

1. Create a new Supabase project at [supabase.com](https://supabase.com).
2. Copy your Project URL and `service_role` key into your backend `.env`.
3. **Database Migration:**
   - Navigate to the SQL Editor in the Supabase dashboard.
   - Copy the contents of `apps/api/app/db/migrations/001_initial_schema.sql` and run it.
4. **Storage Bucket:**
   - Create a new bucket named `utility-bills`.
   - Ensure it is private (or public depending on your signed URL strategy).
5. **Seeding Data:**
   - Manually insert at least one PLC, one SME tied to that PLC, and one Authorized Email tied to that SME to test the webhook.

## Email Webhook Setup

1. Use Postmark or SendGrid to route incoming emails to a webhook.
2. Configure the inbound email address (e.g., `submit@smebridge.com`).
3. Set the webhook URL to your publicly exposed local API (see Tunnel Setup below): `https://<your-tunnel-url>/webhook/incoming-email`.

## Tunnel Setup (Cloudflare Tunnel or Ngrok)

To expose your local FastAPI backend to the email webhook provider:

**Using Ngrok:**
```bash
ngrok http 8000
```
Copy the generated `https` URL and append `/webhook/incoming-email` for your email provider.

**Using Cloudflare Tunnel:**
```bash
cloudflared tunnel --url http://localhost:8000
```

## Local LLM Setup

1. Install [Ollama](https://ollama.ai).
2. Start Ollama and pull the required model:
   ```bash
   ollama run gemma2
   ```
3. The API will communicate with Ollama at `http://localhost:11434`.
4. *Test Fallback*: If you don't have GPU resources locally, use `FakeLLMClient` in your tests to bypass real inference.

## Local Backend Runbook

1. Install dependencies: `cd apps/api && pip install -r requirements-dev.txt`
2. Run the FastAPI development server: `uvicorn app.main:app --reload`
3. In a separate terminal, run the background worker to process bills: `python -m app.processing.worker --max-items 10`
4. Run tests: `pytest`

## Local Frontend Runbook

1. Install dependencies: `cd apps/web && npm install`
2. Run the Vite development server: `npm run dev`
3. Run tests: `npm run test`

## Hardware Stress Test

To perform the VRAM stress test on local hardware:
1. Prepare a dense 15-page PDF utility bill.
2. Submit it via the webhook or insert it directly as a pending bill.
3. Run the worker process while monitoring VRAM:
   ```bash
   watch -n 1 nvidia-smi
   ```
4. Confirm that the memory usage drops between each page processing step as `clear_gpu_cache` is called.

## Known MVP Limitations

- **File Types:** Currently supports PDF, PNG, and JPEG.
- **Provider Master List:** Hardcoded to specific Malaysian providers (TNB, Air Selangor, etc.).
- **Emission Factors:** Hardcoded for MVP rather than fetched from an external dynamic source.
- **Auth:** The MVP lacks a full user authentication flow; current user behavior is mocked.
- **Hardware Dependency:** Requires a local GPU (RTX 3060 6GB recommended minimum) for local inference.
