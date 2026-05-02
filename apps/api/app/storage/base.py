from typing import Protocol, Optional
from pydantic import BaseModel

class StoredFile(BaseModel):
    url_or_path: str
    content_type: str
    size_bytes: int

class StorageService(Protocol):
    def save_raw_attachment(self, sme_id: str, bill_id: str, filename: str, content_type: str, data: bytes) -> StoredFile:
        """
        Saves a raw utility bill attachment to storage.
        Returns a StoredFile containing the persistent path/url.
        """
        ...

    def get_file(self, file_url_or_path: str) -> Optional[bytes]:
        """
        Retrieves the raw bytes of a stored file, if it exists.
        """
        ...

    def maybe_get_public_or_signed_url(self, file_url_or_path: str) -> Optional[str]:
        """
        Returns a public or signed URL if supported by the storage backend, 
        otherwise returns the local path or None.
        """
        ...
