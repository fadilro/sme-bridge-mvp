from app.processing.extraction_parser import parse_llm_extraction, aggregate_page_extractions, ExtractedBillData

def test_parse_clean_json() -> None:
    raw = '{"provider": "TNB", "usage_value": 123.4, "usage_unit": "kWh", "confidence": "high"}'
    result = parse_llm_extraction(raw)
    assert result is not None
    assert result.provider == "TNB"
    assert result.usage_value == 123.4

def test_parse_markdown_fence() -> None:
    raw = "Here is the data:\n```json\n" + \
          '{"provider": "TNB", "usage_value": 100, "usage_unit": "kWh", "confidence": "high"}' + \
          "\n```\nHope it helps."
    result = parse_llm_extraction(raw)
    assert result is not None
    assert result.usage_value == 100

def test_parse_broken_json() -> None:
    assert parse_llm_extraction("{not json}") is None

def test_parse_missing_fields() -> None:
    # missing usage_unit
    raw = '{"provider": "TNB", "usage_value": 123.4, "confidence": "high"}'
    assert parse_llm_extraction(raw) is None

def test_aggregate_confidence_preference() -> None:
    low = ExtractedBillData(provider="TNB", usage_value=10, usage_unit="kWh", confidence="low")
    high = ExtractedBillData(provider="TNB", usage_value=20, usage_unit="kWh", confidence="high")
    
    # prefers high
    assert aggregate_page_extractions([low, high]) == high
    assert aggregate_page_extractions([high, low]) == high

def test_aggregate_all_none() -> None:
    assert aggregate_page_extractions([None, None]) is None

def test_aggregate_provider_preference() -> None:
    no_provider = ExtractedBillData(provider=None, usage_value=10, usage_unit="kWh", confidence="high")
    with_provider = ExtractedBillData(provider="TNB", usage_value=10, usage_unit="kWh", confidence="high")
    
    assert aggregate_page_extractions([no_provider, with_provider]) == with_provider
