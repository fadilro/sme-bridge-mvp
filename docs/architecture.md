# SME Bridge Webhook Architecture

## Webhook Lifecycle

The webhook process strictly isolates receiving raw data from the heavy lifting of extraction:

1. **Receive:** Postmark HTTP POST hits `/webhook/incoming-email`.
2. **Parse:** Extracts attachments from the base64 payload. Missing critical fields result in a `422 Unprocessable Entity`.
3. **Authorize:** Checks the `From` address against our Supabase `smes` authorized emails list. If unauthorized, we bounce and return a `200 OK` so Postmark does not retry.
4. **Persist:** Saves the raw attachments to storage, returning unique file URLs.
5. **Enqueue:** Inserts rows into the `utility_bills` table with a `pending` status.

## Why is extraction asynchronous?
LLM inferences (via Ollama or similar models) can take anywhere from seconds to over a minute, depending on the document size and context. If we attempted to extract data in the webhook response cycle:
- Webhook limits (usually 10-30 seconds) would frequently timeout, triggering the provider's retry logic.
- The provider would re-send identical data, causing duplicated bills and unnecessary LLM costs.

By saving the raw files and returning `200 OK` instantaneously, we prevent timeouts and duplicated effort. The background worker will pick up the `pending` rows entirely decoupled from the email provider's delivery cycle.
