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
from species.species_registry import get_species

#--------------------------------------------------
# Alert Logic
#--------------------------------------------------

def build_alert_result(
    aoi_key: str,
    species_key: str,
    species: dict,
    observations: list
) -> dict:
    """
    Build a structured result for the alert system.
    """

    observation_count = len(observations)

    return {
        "aoi": aoi_key,
        "species": species_key,
        "common_name": species["common_name"],
        "scientific_name": species["scientific_name"],
        "taxon_id": species["taxon_id"],
        "observation_count": observation_count,
        "should_send_alert": observation_count > 0,
        "observations": observations
    }

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

    selected_species = get_species(
    species_name
    )

    alert_result = build_alert_result(
    aoi_key=aoi_name,
    species_key=species_name,
    species=selected_species,
    observations=observations
    )

    print("\nALERT TEST")
    print("=" * 60)

    print(
        "AOI:",
        alert_result["aoi"]
    )

    print(
        "Species:",
        alert_result["species"]
    )

    print(
        "Common Name:",
        alert_result["common_name"]
    )

    print(
        "Observations:",
        alert_result["observation_count"]
    )

    print(
        "Should send alert:",
        alert_result["should_send_alert"]
    )