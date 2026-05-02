import re
from pathlib import Path
from typing import Optional
from supabase import Client
from app.storage.base import StorageService, StoredFile
from app.core.config import settings

class SupabaseStorageService(StorageService):
    def __init__(self, client: Client):
        self.client = client
        self.bucket = settings.SUPABASE_STORAGE_BUCKET

    def _sanitize_filename(self, filename: str) -> str:
        filename = Path(filename).name
        clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
        return clean

    def save_raw_attachment(self, sme_id: str, bill_id: str, filename: str, content_type: str, data: bytes) -> StoredFile:
        safe_filename = self._sanitize_filename(filename)
        object_path = f"utility-bills/raw/{sme_id}/{bill_id}/{safe_filename}"
        
        self.client.storage.from_(self.bucket).upload(
            file=data,
            path=object_path,
            file_options={"content-type": content_type}
        )
        
        # Return the logical path, not the public URL, so we can fetch it securely later
        return StoredFile(
            url_or_path=object_path,
            content_type=content_type,
            size_bytes=len(data)
        )

    def get_file(self, file_url_or_path: str) -> Optional[bytes]:
        try:
            res = self.client.storage.from_(self.bucket).download(file_url_or_path)
            return res
        except Exception:
            return None

    def maybe_get_public_or_signed_url(self, file_url_or_path: str) -> Optional[str]:
        # Using get_public_url for MVP. For private buckets, create_signed_url should be used.
        try:
            return self.client.storage.from_(self.bucket).get_public_url(file_url_or_path)
        except Exception:
            return None
