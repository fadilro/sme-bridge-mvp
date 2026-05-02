# Operations & Setup Guide

## Email Ingestion Setup
The system is designed to work with **Postmark** (recommended) or any email provider that can POST JSON webhooks.

- **Inbound Address:** `submit@yourdomain.com`
- **Webhook URL:** `https://api.yourdomain.com/webhook/incoming-email`
- **Security:** Ensure the endpoint is exposed via HTTPS. Use a secret token in the payload or IP whitelisting for production.
- **Unauthorized Senders:** Senders not found in the `authorized_emails` table will receive an automated bounce notification (if configured).

## Local Tunneling (Development)
To test webhooks locally:
1. Use **Cloudflare Tunnel** (recommended) or **ngrok**.
2. Map your local port 8000:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
3. Use the generated URL as your Postmark webhook destination.

## Seeding Data
To get started, you must seed at least one PLC and one SME.
1. Insert into `plcs` table.
2. Insert into `smes` table (linked to PLC).
3. Insert into `authorized_emails` (linked to SME).

## Monitoring & Logs
- **Backend:** Logs are output to `stdout`.
- **Worker:** Logs processing success/failure for every bill.
- **Supabase:** Check the `utility_bills` table to monitor extraction status in real-time.
