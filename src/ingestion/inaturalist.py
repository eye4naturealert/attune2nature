#--------------------------------------------------
# Imports
#--------------------------------------------------

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import time

import geopandas as gpd
import pandas as pd
import requests

from shapely.geometry import Point


#--------------------------------------------------
# iNaturalist API Settings
#--------------------------------------------------

INATURALIST_URL = (
    "https://api.inaturalist.org/v1/observations"
)

HEADERS = {
    "User-Agent": "Attune2Nature/1.0"
}


#--------------------------------------------------
# Allow Imports from the src Folder
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
# Query iNaturalist by Bounding Box
#--------------------------------------------------

def query_inaturalist_by_bbox(
    bbox: dict,
    taxon_id: int,
    lookback_hours: int = 8760
) -> dict:
    """
    Query all available pages of iNaturalist
    observations using an AOI bounding box.
    """

    since = (
        datetime.now(timezone.utc)
        - timedelta(hours=lookback_hours)
    )

    all_results = []

    page = 1
    per_page = 200
    total_results = 0

    while True:

        params = {
            "swlat": bbox["south"],
            "swlng": bbox["west"],
            "nelat": bbox["north"],
            "nelng": bbox["east"],

            "taxon_id": taxon_id,

            "created_d1": since.isoformat(
                timespec="seconds"
            ),

            "per_page": per_page,
            "page": page,

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

        data = response.json()

        page_results = data.get(
            "results",
            []
        )

        total_results = data.get(
            "total_results",
            0
        )

        print(
            f"Page {page}: "
            f"{len(page_results)} observations"
        )

        all_results.extend(
            page_results
        )

        if len(page_results) < per_page:
            break

        time.sleep(1)

        page += 1

    return {
        "total_results": total_results,
        "results": all_results
    }


#--------------------------------------------------
# Query iNaturalist by Place ID
#--------------------------------------------------

def query_inaturalist_by_place_id(
    place_id: int,
    taxon_id: int,
    lookback_hours: int = 8760
) -> dict:
    """
    Query all available pages of iNaturalist
    observations using an iNaturalist place ID.
    """

    since = (
        datetime.now(timezone.utc)
        - timedelta(hours=lookback_hours)
    )

    all_results = []

    page = 1
    per_page = 200
    total_results = 0

    while True:

        params = {
            "place_id": place_id,
            "taxon_id": taxon_id,

            "created_d1": since.isoformat(
                timespec="seconds"
            ),

            "per_page": per_page,
            "page": page,

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

        data = response.json()

        page_results = data.get(
            "results",
            []
        )

        total_results = data.get(
            "total_results",
            0
        )

        print(
            f"Page {page}: "
            f"{len(page_results)} observations"
        )

        all_results.extend(
            page_results
        )

        if len(page_results) < per_page:
            break

        time.sleep(1)

        page += 1

    return {
        "total_results": total_results,
        "results": all_results
    }


#--------------------------------------------------
# Filter Public Observations to Exact AOI Geometry
#--------------------------------------------------

def filter_observations_to_aoi(
    observations: list[dict],
    aoi_gdf: gpd.GeoDataFrame
) -> dict:
    """
    Keep public iNaturalist observations whose
    coordinates fall inside or touch the exact AOI.

    Obscured observations are separated because their
    displayed coordinates are not their true locations.
    """

    if aoi_gdf.crs is None:
        raise ValueError(
            "AOI geometry does not have a CRS."
        )

    aoi_gdf = aoi_gdf.to_crs(
        "EPSG:4326"
    )

    aoi_geometry = (
        aoi_gdf.geometry.union_all()
    )

    inside_aoi = []
    obscured_observations = []
    missing_coordinates = []

    for observation in observations:

        geoprivacy = observation.get(
            "geoprivacy"
        )

        obscured = observation.get(
            "obscured",
            False
        )

        if (
            geoprivacy == "obscured"
            or obscured
        ):
            obscured_observations.append(
                observation
            )

            continue

        geojson = observation.get(
            "geojson"
        )

        if not geojson:
            missing_coordinates.append(
                observation
            )

            continue

        coordinates = geojson.get(
            "coordinates"
        )

        if (
            not coordinates
            or len(coordinates) < 2
        ):
            missing_coordinates.append(
                observation
            )

            continue

        longitude, latitude = coordinates

        observation_point = Point(
            longitude,
            latitude
        )

        if aoi_geometry.covers(
            observation_point
        ):
            inside_aoi.append(
                observation
            )

    return {
        "inside_aoi": inside_aoi,
        "obscured": obscured_observations,
        "missing_coordinates": missing_coordinates
    }


#--------------------------------------------------
# Fetch Observations for Selected AOI
#--------------------------------------------------

def fetch_observations_for_aoi(
    aoi_name: str,
    species_name: str,
    lookback_hours: int = 8760
) -> dict:
    """
    Wrapper function that reads the AOI registry
    and automatically chooses the correct workflow.

    place_id:
        Query using the registered iNaturalist place ID.

    polygon:
        Query by bounding box and then filter public
        observations against the exact AOI geometry.
    """

    aoi = get_aoi(
        aoi_name
    )

    species = get_species(
        species_name
    )

    search_method = aoi.get(
        "search_method"
    )

    taxon_id = species[
        "taxon_id"
    ]

    print("\nSelected AOI:")
    print(aoi)

    print("\nSelected Species:")
    print(species)

    print(
        "\nSearch Method:",
        search_method
    )

    #----------------------------------------------
    # Place-ID Workflow
    #----------------------------------------------

    if search_method == "place_id":

        place_id = aoi.get(
            "inaturalist_place_id"
        )

        if place_id is None:
            raise ValueError(
                f"AOI '{aoi_name}' uses place_id "
                f"but has no registered place ID."
            )

        print(
            "\nQuerying iNaturalist "
            "by place ID..."
        )

        response = (
            query_inaturalist_by_place_id(
                place_id=place_id,
                taxon_id=taxon_id,
                lookback_hours=lookback_hours
            )
        )

        observations = response.get(
            "results",
            []
        )

        return {
            "aoi_name": aoi_name,
            "species_name": species_name,
            "search_method": "place_id",
            "total_results": response.get(
                "total_results",
                0
            ),
            "observations": observations,
            "obscured_regional": [],
            "missing_coordinates": [],
            "bbox_candidates": None
        }

    #----------------------------------------------
    # Polygon Workflow
    #----------------------------------------------

    if search_method == "polygon":

        print(
            "\nLoading AOI geometry..."
        )

        aoi_gdf = prepare_aoi(
            aoi_name
        )

        bbox = get_aoi_bbox(
            aoi_gdf
        )

        print("\nAOI Bounding Box:")
        print("West :", bbox["west"])
        print("South:", bbox["south"])
        print("East :", bbox["east"])
        print("North:", bbox["north"])

        print(
            "\nQuerying iNaturalist "
            "by bounding box..."
        )

        response = (
            query_inaturalist_by_bbox(
                bbox=bbox,
                taxon_id=taxon_id,
                lookback_hours=lookback_hours
            )
        )

        bbox_results = response.get(
            "results",
            []
        )

        print(
            "\nFiltering public observations "
            "to exact AOI geometry..."
        )

        filtered_results = (
            filter_observations_to_aoi(
                observations=bbox_results,
                aoi_gdf=aoi_gdf
            )
        )

        return {
            "aoi_name": aoi_name,
            "species_name": species_name,
            "search_method": "polygon",
            "total_results": response.get(
                "total_results",
                0
            ),
            "observations":
                filtered_results["inside_aoi"],
            "obscured_regional":
                filtered_results["obscured"],
            "missing_coordinates":
                filtered_results[
                    "missing_coordinates"
                ],
            "bbox_candidates":
                len(bbox_results)
        }

    raise ValueError(
        f"Unsupported search method "
        f"'{search_method}' for AOI "
        f"'{aoi_name}'."
    )


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
        bool(
            observation.get(
                "obscured",
                False
            )
        )
        for observation in results
    )

    public_count = (
        len(results)
        - obscured_count
    )

    print(f"\n{title}")
    print("=" * 90)

    print(
        f"Observations Examined : "
        f"{len(results)}"
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
# Export Observations to CSV
#--------------------------------------------------

def export_observations_to_csv(
    observations: list[dict],
    aoi_name: str,
    species_name: str
) -> Path:
    """
    Export observations with coordinate fields
    suitable for loading into QGIS.
    """

    species = get_species(
        species_name
    )

    export_rows = []

    for observation in observations:

        geojson = (
            observation.get("geojson")
            or {}
        )

        coordinates = (
            geojson.get("coordinates")
            or [None, None]
        )

        export_rows.append({
            "observation_id":
                observation.get("id"),

            "species_common":
                species["common_name"],

            "species_scientific":
                species["scientific_name"],

            "observed_on":
                observation.get("observed_on"),

            "created_at":
                observation.get("created_at"),

            "latitude":
                coordinates[1],

            "longitude":
                coordinates[0],

            "place_guess":
                observation.get("place_guess"),

            "quality_grade":
                observation.get("quality_grade"),

            "obscured":
                observation.get("obscured"),

            "positional_accuracy":
                observation.get(
                    "positional_accuracy"
                ),

            "uri":
                observation.get("uri")
        })

    dataframe = pd.DataFrame(
        export_rows
    )

    # Save into:
    # attune2nature/data/exports
    export_folder = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "exports"
    )

    export_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # Example:
    # 20260805_170423
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_path = (
        export_folder
        / (
            f"{aoi_name}_"
            f"{species_name}_"
            f"inside_aoi_"
            f"{timestamp}.csv"
        )
    )

    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    return output_path.resolve()


#--------------------------------------------------
# Test Section
#--------------------------------------------------

if __name__ == "__main__":

    # Change these values to test another
    # AOI and species combination.
    aoi_name = "loudoun"
    species_name = "common_snapping_turtle"

    # 8760 hours = 365 days
    lookback_hours = 8760

    results = fetch_observations_for_aoi(
        aoi_name=aoi_name,
        species_name=species_name,
        lookback_hours=lookback_hours
    )

    observations = results[
        "observations"
    ]

    summarize_results(
        observations,
        "FINAL AOI OBSERVATION SUMMARY"
    )

    print("\nWORKFLOW SUMMARY")
    print("=" * 90)

    print(
        "Search method          :",
        results["search_method"]
    )

    print(
        "Final observations     :",
        len(observations)
    )

    # These values only apply to polygon AOIs.
    if (
        results["search_method"]
        == "polygon"
    ):
        print(
            "Bounding-box candidates:",
            results["bbox_candidates"]
        )

        print(
            "Obscured regional only:",
            len(
                results[
                    "obscured_regional"
                ]
            )
        )

        print(
            "Missing coordinates   :",
            len(
                results[
                    "missing_coordinates"
                ]
            )
        )

    # Export results for both polygon
    # and place-ID workflows.
    output_csv = (
        export_observations_to_csv(
            observations=observations,
            aoi_name=aoi_name,
            species_name=species_name
        )
    )

    print(
        f"\nExported "
        f"{len(observations)} "
        f"observations to:"
    )

    print(output_csv)