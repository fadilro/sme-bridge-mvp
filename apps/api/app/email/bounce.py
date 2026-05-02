import logging
from typing import Protocol

logger = logging.getLogger(__name__)

class BounceEmailService(Protocol):
    def send_unauthorized_sender_notice(self, to_email: str) -> None:
        """
        Sends an email notice to an unauthorized sender indicating their bill
        submission was rejected.
        """
        ...

class NoopBounceEmailService(BounceEmailService):
    """
    A fake implementation for local development and testing.
    It logs the bounce attempt but does not send a real email.
    """
    def send_unauthorized_sender_notice(self, to_email: str) -> None:
        logger.info(f"Mock bounce notice sent to unauthorized sender: {to_email}")
        # Does not crash or throw exceptions
