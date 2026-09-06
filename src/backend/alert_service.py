# --------------------------------------------------
# Imports
# --------------------------------------------------

from src.alert_logic import run_alert
from src.backend.time_intervals import TIME_INTERVALS, get_time_interval_options
from src.spatial.aoi_registry import get_aoi_options
from src.species.species_registry import get_species_options

# --------------------------------------------------
# Alert Service
# --------------------------------------------------

def process_alert_request(
    aoi_name: str,
    species_name: str,
    time_interval: str
) -> dict:

    if time_interval not in TIME_INTERVALS:
        raise ValueError(
            f"Invalid time interval: {time_interval}"
        )

    interval = TIME_INTERVALS[time_interval]

    lookback_hours = interval["hours"]

    result = run_alert(
        aoi_name=aoi_name,
        species_name=species_name,
        lookback_hours=lookback_hours
    )

    return result

# --------------------------------------------------
# Website Options
# --------------------------------------------------

def get_alert_options() -> dict:

    return {
        "aois": get_aoi_options(),
        "species": get_species_options(),
        "time_intervals": get_time_interval_options()
    }