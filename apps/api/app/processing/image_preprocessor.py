import io
from PIL import Image, ImageOps

def preprocess_page_image(image: Image.Image, max_dimension: int = 1024) -> Image.Image:
    """
    Normalizes a page image for LLM extraction:
    1. Resizes while preserving aspect ratio (max 1024px).
    2. Converts to grayscale.
    3. Applies contrast enhancement.
    4. Binarizes using a global threshold as a fallback for adaptive thresholding.
    """
    # 1. Resize if necessary
    width, height = image.size
    if width > max_dimension or height > max_dimension:
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        
        # Use Lanczos for high-quality downscaling
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 2. Convert to grayscale
    grayscale = image.convert("L")

    # 3. Enhance contrast
    enhanced = ImageOps.autocontrast(grayscale)

    # 4. Threshold (Global threshold at 128 as fallback)
    # This turns it into a clear black-and-white (binary) image
    # suitable for cleaner OCR/extraction.
    threshold = 128
    binary = enhanced.point(lambda p: 255 if p > threshold else 0, mode='1')

    return binary

def encode_image_to_png(image: Image.Image) -> bytes:
    """
    Encodes a PIL image to PNG bytes for transport/storage.
    """
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
