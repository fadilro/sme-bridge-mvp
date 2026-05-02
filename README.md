# SME Bridge MVP

A B2B SaaS platform for the Malaysian ESG sector that solves the Scope 3 data collection bottleneck. It allows SME suppliers to submit utility bills via a zero-friction email gateway. The system extracts "Audit-Ready" CO2e data, permanently linked to the source image, formatted for Bursa Malaysia's CSI platform.

## Architecture
See `docs/architecture.md` for a detailed breakdown of the system components.

## Prerequisites
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)
- [Ollama](https://ollama.com/) (for local LLM extraction)
- A Supabase Project (for PostgreSQL and Storage)

---

## 1. Backend Setup

1. Change into the API directory:
   ```bash
   cd apps/api
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Run tests to verify the baseline:
   ```bash
   pytest
   ```

## 2. Infrastructure & Configuration

### A. Environment Variables
The backend is configured via environment variables. Create an `apps/api/.env` file:
```env
APP_ENV=development
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_STORAGE_BUCKET=test-bucket
OLLAMA_BASE_URL=http://localhost:11434
GEMMA_MODEL_NAME=gemma:2b
POSTMARK_SERVER_TOKEN=your_token
EMAIL_BOUNCE_SENDER=noreply@smebridge.com
EMISSION_FACTOR_ELECTRICITY_KWH=0.58
```

### B. Database & Storage (Supabase)
1. **Database:** Apply the SQL migration located in `apps/api/app/db/migrations/001_initial_schema.sql` to your Supabase project.
2. **Storage:** Manually create a new storage bucket in your Supabase dashboard named `test-bucket` (or whatever you set `SUPABASE_STORAGE_BUCKET` to). Make sure it is public if you want the dashboard image viewer to work out-of-the-box.
3. **Seed Data:** Before testing emails, manually insert at least one `plcs` row, one `smes` row, and one `authorized_emails` row into your database. Only emails matching the `authorized_emails` whitelist will be processed!

### C. Local LLM (Ollama)
1. Install [Ollama](https://ollama.com/).
2. Pull the Gemma model exactly as named in your `.env` file:
   ```bash
   ollama run gemma:2b
   ```
3. Ensure the Ollama server is running (usually backgrounded automatically, running on `http://localhost:11434`).

### D. Exposing Webhooks (For Real Emails)
If you are hooking up a real email provider (like Postmark or SendGrid), they cannot reach `localhost`. 
1. Use a tool like [Ngrok](https://ngrok.com/) or Cloudflare Tunnels:
   ```bash
   ngrok http 8000
   ```
2. In your email provider's dashboard, set the Inbound Webhook URL to `https://<your-ngrok-id>.ngrok.app/webhook/incoming-email`.

---

## 3. Frontend Setup

1. Change into the web directory:
   ```bash
   cd apps/web
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. **Frontend Configuration:** Create an `apps/web/.env` file so the dashboard knows how to reach your FastAPI backend:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

---

## 4. Running the Application Locally

You will need three terminal windows to run the complete MVP locally:

**Terminal 1: FastAPI Server**
```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2: Background Worker (GPU Intensive)**
```bash
cd apps/api
source .venv/bin/activate
# Run continuously to watch the queue
python -m app.processing.worker
# Or process a single item
# python -m app.processing.worker --once
```

**Terminal 3: React Dashboard**
```bash
cd apps/web
npm run dev
```

---

## Deployment
- **Backend:** Designed for containerization. A Dockerfile can easily wrap the FastAPI server.
- **Frontend:** Single Page Application (SPA). Deploy to Vercel, Netlify, or AWS S3/Cloudfront.
- **Worker:** Recommended to run as a separate process (e.g., Celery worker or standalone cron) on an instance with sufficient VRAM (minimum 6GB).

## Features
- **Zero-Friction Ingestion:** SMEs simply email their bills.
- **Human-In-The-Loop:** Visual verification interface for low-confidence extractions.
- **Audit-Ready Exports:** One-click CSV and PDF reporting.
- **Carbon Intelligence:** Automatic emission calculation based on region-specific factors.
