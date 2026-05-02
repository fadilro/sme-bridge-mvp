MALAYSIAN_UTILITY_PROVIDERS = [
    "TNB",
    "Air Selangor",
    "Sarawak Energy",
    "Sabah Electricity",
    "Indah Water"
]

def normalize_provider_name(value: str) -> str:
    """
    Normalizes a provider name by stripping whitespace and returning lowercase.
    This facilitates case-insensitive and stable matching.
    """
    return value.strip().lower()

def is_known_provider(value: str) -> bool:
    """
    Checks if the given provider name matches any known provider.
    """
    normalized_input = normalize_provider_name(value)
    for provider in MALAYSIAN_UTILITY_PROVIDERS:
        if normalize_provider_name(provider) == normalized_input:
            return True
    return False
