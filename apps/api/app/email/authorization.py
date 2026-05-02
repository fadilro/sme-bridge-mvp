from typing import Optional, Dict, Any
from app.db.repositories import SmeRepository

class EmailAuthorizationService:
    def __init__(self, sme_repository: SmeRepository):
        self.sme_repository = sme_repository

    def authorize_sender(self, from_email: str) -> Optional[Dict[str, Any]]:
        """
        Validates if an email address is authorized.
        Returns the SME dict if authorized, otherwise None.
        """
        if not from_email:
            return None
            
        clean_email = from_email.strip().lower()
        return self.sme_repository.find_sme_by_authorized_email(clean_email)
