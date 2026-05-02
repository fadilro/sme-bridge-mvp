from typing import Protocol, Sequence, Union, List
import base64
import httpx
from app.processing.errors import LLMInferenceError

class LLMClient(Protocol):
    def extract_bill_data(self, image_png_bytes: bytes, prompt: str) -> str:
        """
        Sends an image and prompt to the LLM and returns the raw response string.
        """
        ...

class FakeLLMClient:
    """
    Mock client that returns predefined responses or raises exceptions.
    """
    def __init__(self, responses: Sequence[Union[str, Exception]]):
        self.responses = list(responses)
        self.call_count = 0
        self.received_prompts: List[str] = []
        self.received_images: List[bytes] = []

    def extract_bill_data(self, image_png_bytes: bytes, prompt: str) -> str:
        self.call_count += 1
        self.received_prompts.append(prompt)
        self.received_images.append(image_png_bytes)

        if not self.responses:
            raise LLMInferenceError("No more mock responses available.")

        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        
        return resp

class OllamaGemmaClient:
    """
    Real client that communicates with a local Ollama server.
    """
    def __init__(self, base_url: str, model_name: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout

    def extract_bill_data(self, image_png_bytes: bytes, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        image_b64 = base64.b64encode(image_png_bytes).decode("utf-8")
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                if "response" not in data:
                    raise LLMInferenceError("Malformed response from Ollama: missing 'response' field")
                
                return str(data["response"])
                
        except httpx.TimeoutException:
            raise LLMInferenceError(f"Ollama request timed out after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            raise LLMInferenceError(f"Ollama returned HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise LLMInferenceError(f"Unexpected error communicating with Ollama: {e}")
