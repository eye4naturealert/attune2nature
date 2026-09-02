# --------------------------------------------------
# Imports
# --------------------------------------------------

from src.alert_logic import run_alert
from src.backend.time_intervals import TIME_INTERVALS

# --------------------------------------------------
# Alert Service
# --------------------------------------------------

def process_alert_request(
    aoi_name: str,
    species_name: str,
    time_interval: str
) -> dict:

    interval = TIME_INTERVALS[time_interval]

    lookback_hours = interval["hours"]

    result = run_alert(
        aoi_name=aoi_name,
        species_name=species_name,
        lookback_hours=lookback_hours
    )

    return result