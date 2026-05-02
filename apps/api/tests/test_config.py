from app.core.config import Settings

def test_settings_load_with_test_defaults() -> None:
    # We can instantiate Settings without any environment variables
    # because of the defaults provided for testing.
    settings = Settings(_env_file=None)  # type: ignore
    
    assert settings.APP_ENV == "test"
    assert settings.SUPABASE_URL == "https://example.supabase.co"
    assert settings.SUPABASE_SERVICE_ROLE_KEY == "test_service_key"
    assert settings.SUPABASE_STORAGE_BUCKET == "test-bucket"
    assert settings.OLLAMA_BASE_URL == "http://localhost:11434"
    assert settings.GEMMA_MODEL_NAME == "gemma:2b"
    assert settings.EMISSION_FACTOR_ELECTRICITY_KWH == 0.58
