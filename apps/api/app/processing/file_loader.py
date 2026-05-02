import logging
from app.storage.base import StorageService
from app.processing.errors import UnreadableFileError

logger = logging.getLogger(__name__)

def load_raw_file(storage_service: StorageService, raw_file_url: str) -> bytes:
    """
    Loads raw bytes from the storage service.
    Translates storage failures into UnreadableFileError.
    """
    try:
        data = storage_service.get_file(raw_file_url)
    except Exception as e:
        logger.error(f"Storage exception loading {raw_file_url}: {e}")
        raise UnreadableFileError(f"Failed to load file from storage: {e}")
        
    if data is None:
        logger.error(f"File not found in storage: {raw_file_url}")
        raise UnreadableFileError("File not found in storage")
        
    return data
