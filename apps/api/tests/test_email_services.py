from unittest.mock import MagicMock
from app.email.authorization import EmailAuthorizationService
from app.email.bounce import NoopBounceEmailService

def test_authorization_service_authorized() -> None:
    mock_repo = MagicMock()
    mock_repo.find_sme_by_authorized_email.return_value = {"id": "sme-123"}
    
    svc = EmailAuthorizationService(mock_repo)
    result = svc.authorize_sender("TEST@EXAMPLE.com  ")
    
    # Should lowercase and strip before hitting repo
    mock_repo.find_sme_by_authorized_email.assert_called_with("test@example.com")
    assert result is not None
    assert result["id"] == "sme-123"

def test_authorization_service_unauthorized() -> None:
    mock_repo = MagicMock()
    mock_repo.find_sme_by_authorized_email.return_value = None
    
    svc = EmailAuthorizationService(mock_repo)
    result = svc.authorize_sender("unknown@example.com")
    
    assert result is None

def test_noop_bounce_service() -> None:
    svc = NoopBounceEmailService()
    # Should not throw any exception
    svc.send_unauthorized_sender_notice("bad@hacker.com")
