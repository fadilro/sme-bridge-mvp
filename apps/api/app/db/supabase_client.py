from supabase import create_client, Client
from app.core.config import Settings

def create_supabase_client(settings: Settings) -> Client:
    """
    Creates and returns a Supabase Client based on application settings.
    This factory pattern ensures the client is not instantiated at import time,
    preventing issues during unit testing where real credentials are not present.
    """
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
    )
