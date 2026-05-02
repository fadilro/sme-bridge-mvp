import base64
import binascii
from typing import List, Optional, Any
from pydantic import BaseModel

class ParsedAttachment(BaseModel):
    filename: str
    content_type: str
    data: bytes
    size_bytes: int

class ParsedInboundEmail(BaseModel):
    from_email: str
    subject: str
    message_id: Optional[str] = None
    attachments: List[ParsedAttachment] = []

class WebhookParsingError(Exception):
    """Raised when the webhook payload is structurally invalid or missing critical fields."""
    pass

def parse_postmark_webhook(payload: dict[str, Any]) -> ParsedInboundEmail:
    """
    Parses a Postmark Inbound Webhook JSON payload.
    Extracts the sender, subject, and decodes any non-inline base64 attachments.
    """
    from_email_raw = payload.get("From")
    if not from_email_raw:
        raise WebhookParsingError("Missing 'From' field in webhook payload")
        
    # Standardize to lowercase. In a real scenario, this might need more robust parsing
    # if the From field is like 'John Doe <john@example.com>'
    # Postmark provides a 'FromFull' object if we need strict email extraction.
    # For MVP, we'll try to use 'From' directly or extract the email part.
    if "<" in from_email_raw and ">" in from_email_raw:
        from_email = from_email_raw.split("<")[1].split(">")[0].strip().lower()
    else:
        from_email = from_email_raw.strip().lower()

    subject = payload.get("Subject", "")
    message_id = payload.get("MessageID")
    
    parsed_attachments: List[ParsedAttachment] = []
    
    attachments_raw = payload.get("Attachments", [])
    if not isinstance(attachments_raw, list):
        attachments_raw = []

    for att in attachments_raw:
        name = att.get("Name")
        content_type = att.get("ContentType", "application/octet-stream")
        content_b64 = att.get("Content")
        content_id = att.get("ContentID")
        
        # Skip if missing core data
        if not name or not content_b64:
            continue
            
        # Skip inline attachments (heuristics: ContentID is usually present for inline images)
        if content_id and content_id.strip():
            continue
            
        try:
            data = base64.b64decode(content_b64, validate=True)
        except binascii.Error:
            raise WebhookParsingError(f"Invalid base64 encoding for attachment: {name}")
            
        parsed_attachments.append(ParsedAttachment(
            filename=name,
            content_type=content_type,
            data=data,
            size_bytes=len(data)
        ))

    return ParsedInboundEmail(
        from_email=from_email,
        subject=subject,
        message_id=message_id,
        attachments=parsed_attachments
    )
