import re
from pathlib import Path
from typing import Optional
from app.storage.base import StorageService, StoredFile

class LocalStorageService(StorageService):
    def __init__(self, base_dir: str = ".data/storage"):
        self.base_dir = Path(base_dir).resolve()
        # Ensure the base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """
        Removes dangerous characters and standardizes the filename.
        """
        # Remove paths if provided
        filename = Path(filename).name
        # Keep only alphanumeric characters, dashes, underscores, and dots
        clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
        return clean

    def _get_safe_path(self, sme_id: str, bill_id: str, safe_filename: str) -> Path:
        """
        Constructs and validates the file path to prevent traversal attacks.
        """
        target_dir = self.base_dir / "utility-bills" / "raw" / sme_id / bill_id
        target_path = target_dir / safe_filename
        
        resolved_path = target_path.resolve()
        
        # Prevent path traversal
        if not str(resolved_path).startswith(str(target_dir.resolve())):
            raise ValueError("Path traversal attempt detected")
            
        return resolved_path

    def save_raw_attachment(self, sme_id: str, bill_id: str, filename: str, content_type: str, data: bytes) -> StoredFile:
        safe_filename = self._sanitize_filename(filename)
        target_path = self._get_safe_path(sme_id, bill_id, safe_filename)
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        target_path.write_bytes(data)
        
        return StoredFile(
            url_or_path=str(target_path),
            content_type=content_type,
            size_bytes=len(data)
        )

    def get_file(self, file_url_or_path: str) -> Optional[bytes]:
        path = Path(file_url_or_path).resolve()
        
        # Ensure they are reading from within base_dir
        if not str(path).startswith(str(self.base_dir)):
            return None
            
        if not path.exists() or not path.is_file():
            return None
            
        return path.read_bytes()

    def maybe_get_public_or_signed_url(self, file_url_or_path: str) -> Optional[str]:
        # Local storage doesn't serve URLs over HTTP in this implementation,
        # so we just return the local file path as the "URL".
        return file_url_or_path
