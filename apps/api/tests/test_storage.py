import pytest
import shutil
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock
from app.storage.local_storage import LocalStorageService
from app.storage.supabase_storage import SupabaseStorageService
from app.core.config import settings

@pytest.fixture
def test_dir() -> Generator[str, None, None]:
    dir_path = ".data/test_storage"
    yield dir_path
    # Teardown
    if Path(dir_path).exists():
        shutil.rmtree(dir_path)

def test_local_storage_sanitize(test_dir: str) -> None:
    svc = LocalStorageService(base_dir=test_dir)
    assert svc._sanitize_filename("valid.pdf") == "valid.pdf"
    assert svc._sanitize_filename("path/to/valid.pdf") == "valid.pdf"
    assert svc._sanitize_filename("../../etc/passwd") == "passwd"
    assert svc._sanitize_filename("bad file name!.pdf") == "bad_file_name_.pdf"

def test_local_storage_save_and_get(test_dir: str) -> None:
    svc = LocalStorageService(base_dir=test_dir)
    data = b"dummy pdf content"
    
    stored = svc.save_raw_attachment("sme1", "bill1", "test.pdf", "application/pdf", data)
    assert stored.content_type == "application/pdf"
    assert stored.size_bytes == len(data)
    
    # Path should include the ids
    assert "sme1" in stored.url_or_path
    assert "bill1" in stored.url_or_path
    assert "test.pdf" in stored.url_or_path
    
    # Read back
    read_data = svc.get_file(stored.url_or_path)
    assert read_data == data

def test_local_storage_path_traversal(test_dir: str) -> None:
    svc = LocalStorageService(base_dir=test_dir)
    # The sanitization should prevent this, but we can test the `_get_safe_path` directly
    # if we force a bad path.
    with pytest.raises(ValueError, match="Path traversal"):
        svc._get_safe_path("sme1", "bill1", "../../../escaped.pdf")

def test_supabase_storage_save() -> None:
    mock_client = MagicMock()
    svc = SupabaseStorageService(mock_client)
    
    data = b"supabase bytes"
    stored = svc.save_raw_attachment("sme2", "bill2", "unsafe !name.pdf", "application/pdf", data)
    
    assert stored.content_type == "application/pdf"
    assert stored.size_bytes == len(data)
    
    expected_path = "utility-bills/raw/sme2/bill2/unsafe__name.pdf"
    assert stored.url_or_path == expected_path
    
    # Verify the SDK was called correctly
    mock_client.storage.from_.assert_called_with(settings.SUPABASE_STORAGE_BUCKET)
    mock_client.storage.from_().upload.assert_called_with(
        file=data,
        path=expected_path,
        file_options={"content-type": "application/pdf"}
    )
