def calculate_co2e(usage_value: float, emission_factor: float) -> float:
    """
    Calculates the CO2e (Carbon Dioxide Equivalent) emissions.
    
    The calculation applies standard mathematical rounding to 2 decimal places
    to align with standard audit reporting formats.
    """
    raw_co2e = usage_value * emission_factor
    return round(raw_co2e, 2)
