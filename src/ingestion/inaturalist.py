#--------------------------------------------------
# Imports
#--------------------------------------------------

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import geopandas as gpd
import requests


#--------------------------------------------------
# iNaturalist API Settings
#--------------------------------------------------

INATURALIST_URL = (
    "https://api.inaturalist.org/v1/observations"
)

PLACE_AUTOCOMPLETE_URL = (
    "https://api.inaturalist.org/v1/places/autocomplete"
)

HEADERS = {
    "User-Agent": "Attune2Nature/1.0"
}


#--------------------------------------------------
# Allow imports from the src folder
#--------------------------------------------------

SRC_DIR = Path(__file__).resolve().parents[1]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from spatial.aoi_registry import get_aoi, load_geometry
from species.species_registry import get_species


#--------------------------------------------------
# Prepare AOI
#--------------------------------------------------

def prepare_aoi(
    aoi_name: str
) -> gpd.GeoDataFrame:
    """
    Load an AOI and convert it to EPSG:4326.

    EPSG:4326 uses latitude and longitude, which is
    the coordinate system expected by iNaturalist.
    """

    aoi_gdf = load_geometry(aoi_name)

    if aoi_gdf.empty:
        raise ValueError(
            f"AOI '{aoi_name}' contains no geometry."
        )

    if aoi_gdf.crs is None:
        raise ValueError(
            f"AOI '{aoi_name}' does not have a CRS."
        )

    return aoi_gdf.to_crs("EPSG:4326")


#--------------------------------------------------
# Calculate AOI Bounding Box
#--------------------------------------------------

def get_aoi_bbox(
    aoi_gdf: gpd.GeoDataFrame
) -> dict[str, float]:
    """
    Calculate the rectangular bounding box
    surrounding an AOI.
    """

    west, south, east, north = (
        aoi_gdf.total_bounds
    )

    return {
        "west": float(west),
        "south": float(south),
        "east": float(east),
        "north": float(north)
    }


#--------------------------------------------------
# Find iNaturalist Place
#--------------------------------------------------

def find_inaturalist_place(
    place_name: str
) -> dict:
    """
    Find an iNaturalist place by exact display name.
    """

    params = {
        "q": place_name
    }

    response = requests.get(
        PLACE_AUTOCOMPLETE_URL,
        params=params,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    results = response.json().get(
        "results",
        []
    )

    if not results:
        raise ValueError(
            f"No iNaturalist place found for "
            f"'{place_name}'."
        )

    print("\nPossible place matches:")
    print("-" * 70)

    for result in results:

        display_name = (
            result.get("display_name")
            or result.get("name")
            or ""
        )

        print(
            result.get("id"),
            "-",
            display_name
        )

    # Return only an exact display-name match
    for result in results:

        display_name = (
            result.get("display_name")
            or result.get("name")
            or ""
        )

        if (
            display_name.lower()
            == place_name.lower()
        ):
            return result

    raise ValueError(
        f"No exact iNaturalist place match found "
        f"for '{place_name}'. "
        f"Review the printed matches."
    )


#--------------------------------------------------
# Query iNaturalist by Bounding Box
#--------------------------------------------------

def test_inaturalist_query(
    bbox: dict,
    taxon_id: int,
    lookback_hours: int = 8760
) -> dict:
    """
    Query one page of iNaturalist observations
    using an AOI bounding box.
    """

    since = (
        datetime.now(timezone.utc)
        - timedelta(hours=lookback_hours)
    )

    params = {

        "swlat": bbox["south"],
        "swlng": bbox["west"],
        "nelat": bbox["north"],
        "nelng": bbox["east"],

        "taxon_id": taxon_id,

        "created_d1": since.isoformat(
            timespec="seconds"
        ),

        "per_page": 200,
        "page": 1,

        "order_by": "created_at",
        "order": "desc"

    }

    response = requests.get(
        INATURALIST_URL,
        params=params,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


#--------------------------------------------------
# Query iNaturalist by Place ID
#--------------------------------------------------

def test_inaturalist_place_query(
    place_id: int,
    taxon_id: int,
    lookback_hours: int = 8760
) -> dict:
    """
    Query one page of iNaturalist observations
    using an iNaturalist place ID.
    """

    since = (
        datetime.now(timezone.utc)
        - timedelta(hours=lookback_hours)
    )

    params = {

        "place_id": place_id,

        "taxon_id": taxon_id,

        "created_d1": since.isoformat(
            timespec="seconds"
        ),

        "per_page": 200,
        "page": 1,

        "order_by": "created_at",
        "order": "desc"

    }

    response = requests.get(
        INATURALIST_URL,
        params=params,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


#--------------------------------------------------
# Summarize Results
#--------------------------------------------------

def summarize_results(
    results: list[dict],
    title: str
) -> None:
    """
    Print public and obscured observation counts.
    """

    obscured_count = sum(
        obs.get("obscured", False)
        for obs in results
    )

    public_count = (
        len(results)
        - obscured_count
    )

    print(f"\n{title}")
    print("=" * 90)
    print(
        f"Observations Examined : {len(results)}"
    )
    print(
        f"Obscured              : "
        f"{obscured_count}"
    )
    print(
        f"Public                : "
        f"{public_count}"
    )


#--------------------------------------------------
# Test Section
#--------------------------------------------------

if __name__ == "__main__":

    # These two locations should refer to
    # the same geographic area.
    aoi_name = "wod"

    place_search_name = (
        "Washington and Old Dominion"
    )

    species_name = "eastern_box_turtle"

    print("\nSelected AOI:")
    print(get_aoi(aoi_name))

    print("\nSelected Species:")
    print(get_species(species_name))

    print("\nLoading AOI geometry...")

    aoi_gdf = prepare_aoi(aoi_name)

    print("Rows:", len(aoi_gdf))
    print("CRS:", aoi_gdf.crs)

    bbox = get_aoi_bbox(aoi_gdf)

    print("\nAOI Bounding Box:")
    print("West :", bbox["west"])
    print("South:", bbox["south"])
    print("East :", bbox["east"])
    print("North:", bbox["north"])

    species = get_species(species_name)


    #--------------------------------------------------
    # Bounding Box Query
    #--------------------------------------------------

    print(
        "\nQuerying iNaturalist "
        "by bounding box..."
    )

    bbox_response = test_inaturalist_query(
        bbox=bbox,
        taxon_id=species["taxon_id"]
    )

    bbox_results = bbox_response.get(
        "results",
        []
    )

    print("\nBOUNDING-BOX API RESPONSE")
    print("-" * 90)
    print(
        "Total Results:",
        bbox_response.get(
            "total_results",
            0
        )
    )
    print(
        "Returned:",
        len(bbox_results)
    )

    summarize_results(
        bbox_results,
        "BOUNDING-BOX QUERY SUMMARY"
    )


    #--------------------------------------------------
    # Place ID Query
    #--------------------------------------------------

    print(
        f"\nFinding {place_search_name} "
        f"in iNaturalist..."
    )

    place = find_inaturalist_place(
        place_search_name
    )

    print(
        "\nMatched Place:",
        place.get("display_name")
    )
    print(
        "Place ID     :",
        place.get("id")
    )

    print(
        "\nQuerying iNaturalist "
        "by place ID..."
    )

    place_response = (
        test_inaturalist_place_query(
            place_id=place["id"],
            taxon_id=species["taxon_id"]
        )
    )

    place_results = place_response.get(
        "results",
        []
    )

    print("\nPLACE-ID API RESPONSE")
    print("-" * 90)
    print(
        "Total Results:",
        place_response.get(
            "total_results",
            0
        )
    )
    print(
        "Returned:",
        len(place_results)
    )

    summarize_results(
        place_results,
        "PLACE-ID QUERY SUMMARY"
    )


    #--------------------------------------------------
    # Compare Observation IDs
    #--------------------------------------------------

    bbox_ids = {
        obs.get("id")
        for obs in bbox_results
    }

    place_ids = {
        obs.get("id")
        for obs in place_results
    }

    shared_ids = (
        bbox_ids
        & place_ids
    )

    bbox_only_ids = (
        bbox_ids
        - place_ids
    )

    place_only_ids = (
        place_ids
        - bbox_ids
    )

    print("\nQUERY COMPARISON")
    print("=" * 90)
    print(
        "Shared observations       :",
        len(shared_ids)
    )
    print(
        "Bounding-box results only :",
        len(bbox_only_ids)
    )
    print(
        "Place-ID results only     :",
        len(place_only_ids)
    )


    #--------------------------------------------------
    # Inspect Place Guess Values
    #--------------------------------------------------

    print("\nFIRST 20 PLACE-ID RESULTS")
    print("=" * 90)

    for obs in place_results[:20]:

        print(
            f"Observation ID: "
            f"{obs.get('id')} | "
            f"Place Guess: "
            f"{obs.get('place_guess')} | "
            f"Obscured: "
            f"{obs.get('obscured')}"
        )