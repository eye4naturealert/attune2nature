#--------------------------------------------------
# Imports
#--------------------------------------------------

from pathlib import Path
import sys


#--------------------------------------------------
# Allow Imports from the src Folder
#--------------------------------------------------

SRC_DIR = Path(__file__).resolve().parents[1]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from ingestion.inaturalist import fetch_observations_for_aoi


#--------------------------------------------------
# Alert Logic
#--------------------------------------------------

def should_send_alert(
    observations: list[dict]
) -> bool:
    """
    Determine whether an alert should be sent.

    Version 1:
    Send an alert if at least one qualifying
    observation was found.
    """

    return len(observations) > 0


#--------------------------------------------------
# Test Section
#--------------------------------------------------

if __name__ == "__main__":

    aoi_name = "wod"
    species_name = "monarch_butterfly"

    # 24 hours
    lookback_hours = 24

    print("\nFetching observations...")

    results = fetch_observations_for_aoi(
        aoi_name=aoi_name,
        species_name=species_name,
        lookback_hours=lookback_hours
    )

    observations = results[
        "observations"
    ]

    alert = should_send_alert(
        observations
    )

    print("\nALERT TEST")
    print("=" * 60)

    print(
        "AOI:",
        aoi_name
    )

    print(
        "Species:",
        species_name
    )

    print(
        "Observations:",
        len(observations)
    )

    print(
        "Should send alert:",
        alert
    )