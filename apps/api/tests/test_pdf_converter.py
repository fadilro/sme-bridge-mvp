import pytest
import io
from PIL import Image
from unittest.mock import patch, MagicMock
from app.processing.pdf_converter import file_to_page_images
from app.processing.errors import UnreadableFileError
from pdf2image.exceptions import PDFPageCountError

def create_dummy_jpeg() -> bytes:
    img = Image.new('RGB', (10, 10), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def test_convert_valid_jpeg() -> None:
    data = create_dummy_jpeg()
    images = file_to_page_images("test.jpg", "image/jpeg", data)
    
    assert len(images) == 1
    assert isinstance(images[0], Image.Image)
    assert images[0].size == (10, 10)

def test_convert_invalid_image() -> None:
    data = b"not an image"
    with pytest.raises(UnreadableFileError, match="could not be identified"):
        file_to_page_images("bad.png", "image/png", data)

def test_unsupported_format() -> None:
    data = b"some csv data"
    with pytest.raises(UnreadableFileError, match="Unsupported file format"):
        file_to_page_images("data.csv", "text/csv", data)

@patch("app.processing.pdf_converter.pdf2image.convert_from_bytes")
def test_convert_valid_pdf(mock_convert: MagicMock) -> None:
    # Mocking pdf2image to avoid poppler dependency strictly during unit tests
    dummy_img = Image.new('RGB', (10, 10))
    mock_convert.return_value = [dummy_img, dummy_img]
    
    data = b"%PDF-1.4 mock pdf data"
    images = file_to_page_images("doc.pdf", "application/pdf", data)
    
    assert len(images) == 2
    mock_convert.assert_called_once_with(data)

@patch("app.processing.pdf_converter.pdf2image.convert_from_bytes")
def test_convert_protected_pdf(mock_convert: MagicMock) -> None:
    mock_convert.side_effect = PDFPageCountError("Unable to get page count")
    
    data = b"%PDF-1.4 mock protected data"
    with pytest.raises(UnreadableFileError, match="password protected or corrupted"):
        file_to_page_images("secret.pdf", "application/pdf", data)
