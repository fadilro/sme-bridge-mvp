from fastapi import Depends
from supabase import Client

from app.core.config import get_settings, Settings
from app.db.supabase_client import create_supabase_client
from app.db.repositories import SmeRepository, UtilityBillRepository
from app.db.supabase_repositories import SupabaseSmeRepository, SupabaseUtilityBillRepository
from app.storage.base import StorageService
from app.storage.supabase_storage import SupabaseStorageService
from app.email.authorization import EmailAuthorizationService
from app.email.bounce import BounceEmailService, NoopBounceEmailService

# Global state for clients to prevent recreation per request
_supabase_client: Client | None = None

def get_supabase_client(settings: Settings = Depends(get_settings)) -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_supabase_client(settings)
    return _supabase_client

def get_sme_repository(client: Client = Depends(get_supabase_client)) -> SmeRepository:
    return SupabaseSmeRepository(client)

def get_utility_bill_repository(client: Client = Depends(get_supabase_client)) -> UtilityBillRepository:
    return SupabaseUtilityBillRepository(client)

def get_storage_service(client: Client = Depends(get_supabase_client)) -> StorageService:
    return SupabaseStorageService(client)

def get_email_authorization_service(
    sme_repo: SmeRepository = Depends(get_sme_repository)
) -> EmailAuthorizationService:
    return EmailAuthorizationService(sme_repo)

def get_bounce_email_service() -> BounceEmailService:
    # For MVP, we are using the Noop service in production as well until postmark is wired up
    return NoopBounceEmailService()

def get_current_user_id() -> str:
    """
    Placeholder dependency for the current authenticated user.
    In the MVP, we assume a single system administrator for HITL tasks.
    """
    return "system_admin"
