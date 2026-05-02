from app.core.config import settings

def get_electricity_emission_factor() -> float:
    """
    Returns the configured emission factor for electricity usage (typically in kWh).
    This value is injected from the application settings to allow for future
    updates or different environments.
    """
    return settings.EMISSION_FACTOR_ELECTRICITY_KWH
