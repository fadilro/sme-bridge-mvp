from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from app.db.repositories import SmeRepository
from app.core.dependencies import get_sme_repository

router = APIRouter(prefix="/smes", tags=["smes"])


@router.get("", response_model=List[Dict[str, Any]])
def list_smes(
    repo: SmeRepository = Depends(get_sme_repository),
) -> List[Dict[str, Any]]:
    """
    Returns all registered SMEs. Used by the frontend to populate the SME selector.
    """
    return repo.list_all_smes()
