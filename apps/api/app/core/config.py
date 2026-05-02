from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.
    Default values are provided to allow tests to run without requiring
    real secrets in the environment.
    """

    APP_ENV: str = "test"
    SUPABASE_URL: str = "https://example.supabase.co"
    SUPABASE_SERVICE_ROLE_KEY: str = "test_service_key"
    SUPABASE_STORAGE_BUCKET: str = "test-bucket"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GEMMA_MODEL_NAME: str = "gemma4:e2b"
    EMISSION_FACTOR_ELECTRICITY_KWH: float = 0.58  # Default test factor

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# Global settings instance to be used across the app
settings = Settings()

def get_settings() -> Settings:
    return settings
