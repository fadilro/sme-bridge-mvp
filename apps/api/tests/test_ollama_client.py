import pytest
from unittest.mock import patch, MagicMock
import httpx
from app.processing.llm_client import OllamaGemmaClient
from app.processing.errors import LLMInferenceError

@patch("httpx.Client")
def test_ollama_success(mock_client_class: MagicMock) -> None:
    # Setup mock response
    mock_client = mock_client_class.return_value.__enter__.return_value
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "{\"provider\": \"TNB\"}"}
    mock_client.post.return_value = mock_response
    
    client = OllamaGemmaClient(base_url="http://mock:11434", model_name="gemma4:e2b")
    result = client.extract_bill_data(b"image_bytes", "extract this")
    
    assert result == "{\"provider\": \"TNB\"}"
    
    # Verify the call
    args, kwargs = mock_client.post.call_args
    assert args[0] == "http://mock:11434/api/generate"
    assert kwargs["json"]["model"] == "gemma4:e2b"
    assert kwargs["json"]["prompt"] == "extract this"
    assert "images" in kwargs["json"]

@patch("httpx.Client")
def test_ollama_http_error(mock_client_class: MagicMock) -> None:
    mock_client = mock_client_class.return_value.__enter__.return_value
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    # Make raise_for_status raise an error
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=mock_response
    )
    mock_client.post.return_value = mock_response
    
    client = OllamaGemmaClient(base_url="http://mock:11434", model_name="gemma4:e2b")
    
    with pytest.raises(LLMInferenceError, match="HTTP error 500"):
        client.extract_bill_data(b"img", "prompt")

@patch("httpx.Client")
def test_ollama_timeout(mock_client_class: MagicMock) -> None:
    mock_client = mock_client_class.return_value.__enter__.return_value
    mock_client.post.side_effect = httpx.TimeoutException("Timeout")
    
    client = OllamaGemmaClient(base_url="http://mock:11434", model_name="gemma4:e2b")
    
    with pytest.raises(LLMInferenceError, match="timed out"):
        client.extract_bill_data(b"img", "prompt")

@patch("httpx.Client")
def test_ollama_malformed_response(mock_client_class: MagicMock) -> None:
    mock_client = mock_client_class.return_value.__enter__.return_value
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"not_response": "oops"}
    mock_client.post.return_value = mock_response
    
    client = OllamaGemmaClient(base_url="http://mock:11434", model_name="gemma4:e2b")
    
    with pytest.raises(LLMInferenceError, match="Malformed response"):
        client.extract_bill_data(b"img", "prompt")
