import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, Body, HTTPException

from app.core.dependencies import (
    get_email_authorization_service,
    get_bounce_email_service,
    get_storage_service,
    get_utility_bill_repository
)
from app.db.repositories import UtilityBillRepository
from app.storage.base import StorageService
from app.email.authorization import EmailAuthorizationService
from app.email.bounce import BounceEmailService
from app.email.webhook_parser import parse_postmark_webhook, WebhookParsingError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhook"])

@router.post("/incoming-email")
def incoming_email_webhook(
    payload: Dict[str, Any] = Body(...),
    auth_service: EmailAuthorizationService = Depends(get_email_authorization_service),
    bounce_service: BounceEmailService = Depends(get_bounce_email_service),
    storage_service: StorageService = Depends(get_storage_service),
    bill_repo: UtilityBillRepository = Depends(get_utility_bill_repository)
) -> Dict[str, Any]:
    
    try:
        parsed_email = parse_postmark_webhook(payload)
    except WebhookParsingError as e:
        logger.warning(f"Invalid webhook payload: {e}")
        # 422 Unprocessable Entity
        raise HTTPException(status_code=422, detail=str(e))
        
    # 1. Authorize sender
    sme = auth_service.authorize_sender(parsed_email.from_email)
    
    if not sme:
        # Sender not found in whitelist
        logger.info(f"Unauthorized sender attempting to submit bills: {parsed_email.from_email}")
        
        # Fire and forget bounce notice
        try:
            bounce_service.send_unauthorized_sender_notice(parsed_email.from_email)
        except Exception as e:
            logger.error(f"Failed to send bounce notice to {parsed_email.from_email}: {e}")
            
        # We return 200 OK so the email provider knows we processed it and doesn't retry
        return {"message": "unauthorized sender ignored"}
        
    sme_id = sme["id"]
    accepted_count = 0
    
    # 2. Process attachments
    for att in parsed_email.attachments:
        try:
            # We don't have the bill_id yet, but we can generate a temporary one or 
            # we can create the pending bill first to get the ID, then save, then update.
            # But the contract for save_raw_attachment requires a bill_id for path generation.
            # The contract for create_pending_utility_bill requires raw_file_url.
            
            # Let's import uuid to generate the bill_id locally
            import uuid
            bill_id = str(uuid.uuid4())
            
            # Save file
            stored_file = storage_service.save_raw_attachment(
                sme_id=sme_id,
                bill_id=bill_id,
                filename=att.filename,
                content_type=att.content_type,
                data=att.data
            )
            
            # If using local dict repo it might ignore our provided ID, but for Supabase we can't easily 
            # insert with a generated ID unless the schema allows it. The schema has `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`.
            # Wait, `create_pending_utility_bill` doesn't take bill_id. It creates it.
            # Let's adjust logic: 
            # For MVP, we can save it to a generic path or we can pass `pending` as the bill_id folder.
            # Actually, the spec says: "create_pending_utility_bill(sme_id, raw_file_url, original_filename)".
            # If we need the bill_id for the storage path, we have a chicken/egg problem.
            # Let's create the record first with a dummy URL, then save the file, then update the record? No, repo doesn't have an update URL method.
            # Let's generate a UUID in Python and use it for BOTH the path and the DB insert. 
            # Oh wait, `create_pending_utility_bill` doesn't take `bill_id`. It generates it or DB generates it.
            # Let's just use a random UUID for the storage path folder. It doesn't strictly need to match the DB row ID if we store the full URL in the DB row!
            
            storage_folder_uuid = str(uuid.uuid4())
            stored_file = storage_service.save_raw_attachment(
                sme_id=sme_id,
                bill_id=storage_folder_uuid,  # Use random uuid for storage folder
                filename=att.filename,
                content_type=att.content_type,
                data=att.data
            )
            
            # Create DB row
            bill_repo.create_pending_utility_bill(
                sme_id=sme_id,
                raw_file_url=stored_file.url_or_path,
                original_filename=att.filename
            )
            
            accepted_count += 1
            
        except Exception as e:
            # Documented behavior: Partial failures should log and continue, 
            # not silent-failing the whole payload.
            logger.error(f"Failed to process attachment {att.filename} for SME {sme_id}: {e}")
            continue

    return {
        "message": "success",
        "accepted_attachments": accepted_count
    }
