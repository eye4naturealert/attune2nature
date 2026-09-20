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

#--------------------------------------------------
# Attune2Nature Imports
#--------------------------------------------------

from src.ingestion.inaturalist import fetch_observations_for_aoi
from src.species.species_registry import get_species
from src.spatial.aoi_registry import get_aoi

#--------------------------------------------------
# Alert Logic
#--------------------------------------------------
def format_observations(
    observations: list
) -> list[dict]:
    """
    Convert raw iNaturalist observations into
    a simplified alert-friendly structure.
    """

    formatted = []

    for obs in observations:

        geojson = obs.get("geojson") or {}
        coordinates = geojson.get("coordinates")

        if coordinates:
            lon, lat = coordinates
        else:
            lon = None
            lat = None

        formatted.append({
            "observation_id": obs.get("id"),
            "observed_on": obs.get("observed_on"),
            "created_at": obs.get("created_at"),
            "quality_grade": obs.get("quality_grade"),
            "observer": obs.get("user", {}).get("login"),
            "latitude": lat,
            "longitude": lon,
            "geoprivacy": obs.get("geoprivacy"),
            "taxon_geoprivacy": obs.get("taxon_geoprivacy"),
            "url": (
                f"https://www.inaturalist.org/observations/"
                f"{obs.get('id')}"
            )
        })

    return formatted

def build_alert_result(
    aoi_key: str,
    species_key: str,
    aoi: dict,
    species: dict,
    observations: list,
    lookback_hours: int
) -> dict:
    """
    Build a structured result for the alert system.
    """

    formatted_observations = format_observations(
        observations
    )

    observation_count = len(formatted_observations)

    return {
        "aoi_key": aoi_key,
        "aoi_name": aoi["name"],
        "species_key": species_key,
        "common_name": species["common_name"],
        "scientific_name": species["scientific_name"],
        "taxon_id": species["taxon_id"],
        "lookback_hours": lookback_hours,
        "observation_count": observation_count,
        "should_send_alert": observation_count > 0,
        "observations": formatted_observations
    }


def run_alert(
    aoi_name: str,
    species_name: str,
    lookback_hours: int
) -> dict:
    """
    Run the complete Attune2Nature alert workflow
    for one AOI and one species.
    """

    results = fetch_observations_for_aoi(
        aoi_name=aoi_name,
        species_name=species_name,
        lookback_hours=lookback_hours
    )

    observations = results["observations"]

    selected_aoi = get_aoi(
        aoi_name
    )

    selected_species = get_species(
        species_name
    )

    alert_result = build_alert_result(
        aoi_key=aoi_name,
        species_key=species_name,
        aoi=selected_aoi,
        species=selected_species,
        observations=observations,
        lookback_hours=lookback_hours
    )

    return alert_result


#--------------------------------------------------
# Test Section
#--------------------------------------------------

if __name__ == "__main__":

    aoi_name = "loudoun"
    species_name = "bald_eagle"

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

    selected_aoi = get_aoi(
        aoi_name
    )

    selected_species = get_species(
        species_name
    )

    alert_result = build_alert_result(
        aoi_key=aoi_name,
        species_key=species_name,
        aoi=selected_aoi,
        species=selected_species,
        observations=observations,
        lookback_hours=lookback_hours
    )

    print("\nALERT RESULT")
    print("=" * 60)

    print(
        "AOI Key:",
        alert_result["aoi_key"]
    )

    print(
        "AOI Name:",
        alert_result["aoi_name"]
    )

    print(
        "Species Key:",
        alert_result["species_key"]
    )

    print(
        "Common Name:",
        alert_result["common_name"]
    )

    print(
        "Scientific Name:",
        alert_result["scientific_name"]
    )

    print(
        "Taxon ID:",
        alert_result["taxon_id"]
    )

    print(
        "Lookback Hours:",
        alert_result["lookback_hours"]
    )

    print(
        "Observations:",
        alert_result["observation_count"]
    )

    print(
        "Should Send Alert:",
        alert_result["should_send_alert"]
    )

    print("\nMATCHING OBSERVATIONS")
    print("=" * 60)

    for obs in alert_result["observations"]:

        print("\nObservation ID:", obs["observation_id"])
        print("Observed On:", obs["observed_on"])
        print("Uploaded:", obs["created_at"])
        print("Quality Grade:", obs["quality_grade"])
        print("Observer:", obs["observer"])
        print("Geoprivacy:", obs["geoprivacy"])
        print("Latitude:", obs["latitude"])
        print("Longitude:", obs["longitude"])
        print("URL:", obs["url"])
    