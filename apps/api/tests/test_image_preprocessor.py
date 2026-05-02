import io
from PIL import Image
from app.processing.image_preprocessor import preprocess_page_image, encode_image_to_png

def test_preprocess_landscape_resize() -> None:
    # 2000x1000 -> 1024x512
    img = Image.new('RGB', (2000, 1000), color='white')
    processed = preprocess_page_image(img, max_dimension=1024)
    
    assert processed.size == (1024, 512)
    # Output should be binary/grayscale mode '1' as implemented
    assert processed.mode == '1'

def test_preprocess_portrait_resize() -> None:
    # 1000x2000 -> 512x1024
    img = Image.new('RGB', (1000, 2000), color='white')
    processed = preprocess_page_image(img, max_dimension=1024)
    
    assert processed.size == (512, 1024)
    assert processed.mode == '1'

def test_preprocess_small_no_resize() -> None:
    # 500x500 -> 500x500
    img = Image.new('RGB', (500, 500), color='white')
    processed = preprocess_page_image(img, max_dimension=1024)
    
    assert processed.size == (500, 500)
    assert processed.mode == '1'

def test_encode_to_png() -> None:
    img = Image.new('RGB', (100, 100), color='red')
    png_bytes = encode_image_to_png(img)
    
    # Check PNG magic number
    assert png_bytes.startswith(b'\x89PNG')
    
    # Ensure it's decodable back to an image
    decoded = Image.open(io.BytesIO(png_bytes))
    assert decoded.size == (100, 100)
