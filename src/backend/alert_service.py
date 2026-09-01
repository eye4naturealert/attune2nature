# --------------------------------------------------
# Imports
# --------------------------------------------------

from src.alert_logic import run_alert


# --------------------------------------------------
# Alert Service
# --------------------------------------------------

def process_alert_request(
    aoi_name: str,
    species_name: str,
    lookback_hours: int
) -> dict:

    result = run_alert(
        aoi_name=aoi_name,
        species_name=species_name,
        lookback_hours=lookback_hours
    )

    return result