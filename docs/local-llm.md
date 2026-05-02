# Local LLM Setup (Ollama)

SME Bridge uses [Ollama](https://ollama.ai/) for local multimodal inference. This allows us to extract structured data from utility bill images without sending sensitive data to 3rd-party cloud providers.

## Configuration

The following environment variables in `apps/api/.env` control the LLM connection:

- `OLLAMA_BASE_URL`: The URL where Ollama is running (default: `http://localhost:11434`).
- `GEMMA_MODEL_NAME`: The specific model to use (default: `gemma4:e2b` or similar multimodal model).

## Setup Instructions

1. **Install Ollama:** Download and install from [ollama.ai](https://ollama.ai/).
2. **Pull the Model:**
   ```bash
   ollama pull gemma4:e2b
   ```
3. **Verify Ollama is Running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Manual Verification

You can verify the client logic by running the worker in `--once` mode with a real `pending` bill in the database:

```bash
cd apps/api
source .venv/bin/activate
python -m app.processing.worker --once
```

## Running Without Ollama

For development and automated testing, the system uses a `FakeLLMClient` that bypasses real network calls. This is controlled by the `APP_ENV` setting. If `APP_ENV=test`, real LLM calls are disabled.
