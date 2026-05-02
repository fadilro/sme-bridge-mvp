import io
import logging
from typing import List
from PIL import Image, UnidentifiedImageError
import pdf2image
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError, PDFInfoNotInstalledError

from app.processing.errors import UnreadableFileError

logger = logging.getLogger(__name__)

def file_to_page_images(filename: str, content_type: str, data: bytes) -> List[Image.Image]:
    """
    Converts a raw file (PDF, PNG, JPEG) into a list of PIL Images.
    For images, the list will contain exactly one item.
    For PDFs, it will contain one item per page.
    """
    filename_lower = filename.lower()
    
    # 1. Handle PDF
    if content_type == "application/pdf" or filename_lower.endswith(".pdf"):
        try:
            # We do not use auto-crop or heavy pre-processing here as the LLM 
            # might need the full context.
            images = pdf2image.convert_from_bytes(data)
            if not images:
                raise UnreadableFileError("PDF yielded zero pages.")
            return images
            
        except PDFPageCountError:
            raise UnreadableFileError("Could not determine PDF page count. It may be password protected or corrupted.")
        except PDFSyntaxError:
            raise UnreadableFileError("PDF syntax error. File is corrupted.")
        except PDFInfoNotInstalledError:
            logger.error("Poppler is not installed on the system.")
            raise UnreadableFileError("System configuration error: Poppler missing.")
        except Exception as e:
            logger.error(f"Unexpected error converting PDF {filename}: {e}")
            raise UnreadableFileError(f"Failed to convert PDF: {e}")

    # 2. Handle Image
    if content_type in ("image/jpeg", "image/png", "image/jpg") or \
       filename_lower.endswith((".jpg", ".jpeg", ".png")):
        try:
            img = Image.open(io.BytesIO(data))
            # Ensure the image is actually loaded and decoded from bytes
            img.load()
            return [img]
        except UnidentifiedImageError:
            raise UnreadableFileError(f"File {filename} could not be identified as a valid image.")
        except Exception as e:
            logger.error(f"Unexpected error loading image {filename}: {e}")
            raise UnreadableFileError(f"Failed to load image: {e}")
            
    # 3. Unsupported format
    raise UnreadableFileError(f"Unsupported file format: {content_type} / {filename}")
