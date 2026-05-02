from fastapi import APIRouter
from typing import Dict

router = APIRouter()

@router.get("/health")
def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    """
    return {
        "status": "ok",
        "service": "sme-bridge-api"
    }
