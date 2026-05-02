import pytest
import base64
from app.email.webhook_parser import parse_postmark_webhook, WebhookParsingError

def test_parse_valid_payload_single_attachment() -> None:
    pdf_content = b"fake pdf content"
    b64_content = base64.b64encode(pdf_content).decode('ascii')
    
    payload = {
        "From": "test@SME.com",
        "Subject": "My Utility Bill",
        "MessageID": "msg-123",
        "Attachments": [
            {
                "Name": "bill.pdf",
                "ContentType": "application/pdf",
                "Content": b64_content
            }
        ]
    }
    
    parsed = parse_postmark_webhook(payload)
    
    assert parsed.from_email == "test@sme.com"
    assert parsed.subject == "My Utility Bill"
    assert parsed.message_id == "msg-123"
    assert len(parsed.attachments) == 1
    
    att = parsed.attachments[0]
    assert att.filename == "bill.pdf"
    assert att.content_type == "application/pdf"
    assert att.data == pdf_content
    assert att.size_bytes == len(pdf_content)

def test_parse_valid_payload_multiple_attachments() -> None:
    att1_bytes = b"jpeg1"
    att2_bytes = b"jpeg2"
    
    payload = {
        "From": "Test User <user@example.com>",
        "Subject": "",
        "Attachments": [
            {
                "Name": "1.jpg",
                "Content": base64.b64encode(att1_bytes).decode('ascii')
            },
            {
                "Name": "2.jpg",
                "Content": base64.b64encode(att2_bytes).decode('ascii')
            }
        ]
    }
    
    parsed = parse_postmark_webhook(payload)
    assert parsed.from_email == "user@example.com"
    assert len(parsed.attachments) == 2
    assert parsed.attachments[0].filename == "1.jpg"
    assert parsed.attachments[1].filename == "2.jpg"

def test_parse_missing_from() -> None:
    payload = {
        "Subject": "No From",
        "Attachments": []
    }
    with pytest.raises(WebhookParsingError, match="Missing 'From' field"):
        parse_postmark_webhook(payload)

def test_parse_invalid_base64() -> None:
    payload = {
        "From": "test@example.com",
        "Attachments": [
            {
                "Name": "bad.pdf",
                "Content": "this is not base64!!!"
            }
        ]
    }
    with pytest.raises(WebhookParsingError, match="Invalid base64 encoding"):
        parse_postmark_webhook(payload)

def test_parse_empty_attachments() -> None:
    payload = {
        "From": "test@example.com",
        "Subject": "No Attachments"
    }
    parsed = parse_postmark_webhook(payload)
    assert len(parsed.attachments) == 0

def test_parse_skips_inline_attachments() -> None:
    att_bytes = b"logo"
    payload = {
        "From": "test@example.com",
        "Attachments": [
            {
                "Name": "logo.png",
                "ContentID": "cid:logo.png",
                "Content": base64.b64encode(att_bytes).decode('ascii')
            },
            {
                "Name": "bill.pdf",
                "Content": base64.b64encode(b"pdf").decode('ascii')
            }
        ]
    }
    parsed = parse_postmark_webhook(payload)
    assert len(parsed.attachments) == 1
    assert parsed.attachments[0].filename == "bill.pdf"
