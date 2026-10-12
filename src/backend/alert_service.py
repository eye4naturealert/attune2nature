
# --------------------------------------------------
# Imports
# --------------------------------------------------

from src.alert_logic import run_alert

from src.backend.time_intervals import (
    TIME_INTERVALS,
    get_time_interval_options
)

from src.spatial.aoi_registry import get_aoi_options

from src.species.species_registry import get_species_options


# --------------------------------------------------
# Process Alert Request
# --------------------------------------------------

def process_alert_request(
    aoi_name: str,
    species_name: str,
    time_interval: str
) -> dict:
    """
    Process a wildlife alert request.
    """

    if time_interval not in TIME_INTERVALS:
        raise ValueError(
            f"Invalid time interval: {time_interval}"
        )

    interval = TIME_INTERVALS[time_interval]

    result = run_alert(
        aoi_name=aoi_name,
        species_name=species_name,
        lookback_hours=interval["hours"]
    )

    result["time_interval_label"] = interval["label"]

    return result


# --------------------------------------------------
# Website Dropdown Options
# --------------------------------------------------

def get_alert_options() -> dict:
    """
    Return AOI, species, and time interval
    options for the website.
    """

    return {
        "aois": get_aoi_options(),
        "species": get_species_options(),
        "time_intervals": get_time_interval_options()
    }
