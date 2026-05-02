import pytest
from app.processing.llm_prompt import build_bill_extraction_prompt
from app.processing.llm_client import FakeLLMClient
from app.processing.errors import LLMInferenceError

def test_prompt_contains_required_keys() -> None:
    prompt = build_bill_extraction_prompt()
    required_keys = ["provider", "billing_period", "usage_value", "usage_unit", "confidence"]
    
    for key in required_keys:
        assert f"'{key}'" in prompt or f"\"{key}\"" in prompt
    
    assert "strict JSON" in prompt
    assert "Malaysian" in prompt

def test_fake_llm_returns_queued_responses() -> None:
    responses = ["{\"resp\": 1}", "{\"resp\": 2}"]
    client = FakeLLMClient(responses)
    
    assert client.extract_bill_data(b"image1", "prompt1") == "{\"resp\": 1}"
    assert client.extract_bill_data(b"image2", "prompt2") == "{\"resp\": 2}"
    assert client.call_count == 2
    assert client.received_prompts == ["prompt1", "prompt2"]

def test_fake_llm_simulates_exception() -> None:
    responses = [LLMInferenceError("Model busy")]
    client = FakeLLMClient(responses)
    
    with pytest.raises(LLMInferenceError, match="Model busy"):
        client.extract_bill_data(b"img", "prompt")
    
    assert client.call_count == 1

def test_fake_llm_empty_queue_raises() -> None:
    client = FakeLLMClient([])
    with pytest.raises(LLMInferenceError, match="No more mock responses"):
        client.extract_bill_data(b"img", "prompt")
