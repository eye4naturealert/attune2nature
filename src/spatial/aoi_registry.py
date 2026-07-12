from pathlib import Path

import geopandas as gpd


#--------------------------------------------------
# Project Root
#--------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]


#--------------------------------------------------
# AOI Registry
#--------------------------------------------------

AOIS = {

    "wod": {

    "name": "Washington & Old Dominion Trail",
    "country": "USA",
    "state": "Virginia",
    "type": "trail",

    "search_method": "polygon",

    "inaturalist_place_id": 195618,

    "geometry":
        BASE_DIR / "data" / "aois" /
        "OSM_W&OD_Trail_25mBuffer.geojson",

    "reference_layers": {

        "mile_markers":
            BASE_DIR / "data" / "reference" /
            "WOD_MileMarkers.geojson"

    }

},


    "loudoun": {

        "name": "Loudoun County",
        "country": "USA",
        "state": "Virginia",
        "type": "county",

        "search_method": "place_id",
        "inaturalist_place_id": 739,

        "geometry":
            BASE_DIR / "data" / "aois" / "LoudounCounty.geojson",

        "reference_layers": {}

    },

    "fairfax": {

        "name": "Fairfax County",
        "country": "USA",
        "state": "Virginia",
        "type": "county",

        "search_method": "place_id",
        "inaturalist_place_id": 738,

        "geometry":
            BASE_DIR / "data" / "aois" / "FairfaxCounty.geojson",

        "reference_layers": {}

    },

    "arlington": {

        "name": "Arlington County",
        "country": "USA",
        "state": "Virginia",
        "type": "county",

        "search_method": "place_id",
        "inaturalist_place_id": 1719,

        "geometry":
            BASE_DIR / "data" / "aois" / "ArlingtonCounty.geojson",

        "reference_layers": {}

    },

    "falls_church": {

        "name": "Falls Church City",
        "country": "USA",
        "state": "Virginia",
        "type": "independent_city",

        "search_method": "place_id",
        "inaturalist_place_id": 13451,

        "geometry":
            BASE_DIR / "data" / "aois" / "FallsChurchCity.geojson",

        "reference_layers": {}

    },

    "alexandria": {

        "name": "Alexandria City",
        "country": "USA",
        "state": "Virginia",
        "type": "independent_city",

        "geometry":
            BASE_DIR / "data" / "aois" / "AlexandriaCity.geojson",

        "search_method": "place_id",
        "inaturalist_place_id": 13446,

        "reference_layers": {}

    }

}

#--------------------------------------------------
# Helper Functions
#--------------------------------------------------

def list_aois() -> list[str]:
    """
    Return a list of available AOI identifiers.
    """
    return list(AOIS.keys())


def get_aoi(name: str) -> dict:
    """
    Return the AOI metadata dictionary.

    Parameters
    ----------
    name : str
        AOI identifier (e.g. 'loudoun').

    Returns
    -------
    dict
        AOI metadata dictionary.
    """
    return AOIS.get(name)


def load_geometry(name: str) -> gpd.GeoDataFrame:
    """
    Load an AOI boundary as a GeoDataFrame.
    """

    aoi = get_aoi(name)

    if aoi is None:
        raise ValueError(
            f"Unknown AOI '{name}'. "
            f"Available AOIs: {', '.join(list_aois())}"
        )

    return gpd.read_file(aoi["geometry"])


def load_mile_markers() -> gpd.GeoDataFrame:
    """
    Load the W&OD Trail mile marker reference layer.
    """

    path = AOIS["wod"]["reference_layers"]["mile_markers"]

    return gpd.read_file(path)


#--------------------------------------------------
# Test Section
#--------------------------------------------------

if __name__ == "__main__":

    print("Project Root:")
    print(BASE_DIR)

    print("\nAvailable AOIs:")
    print(list_aois())

    print("\nTesting get_aoi():")
    print(get_aoi("loudoun"))

    print("\nAOI Files:")

    for key, aoi in AOIS.items():
        print(f"\n{key}")
        print(aoi["geometry"])
        print("Exists:", aoi["geometry"].exists())

    print("\nTesting geometry loading:")

    for aoi_name in list_aois():

        print(f"\nLoading: {aoi_name}")

        gdf = load_geometry(aoi_name)

        print("Rows:", len(gdf))
        print("CRS:", gdf.crs)
        print("Geometry type:", gdf.geometry.geom_type.iloc[0])

    print("\nTesting mile markers:")

    mile_markers = load_mile_markers()

    print("Rows:", len(mile_markers))
    print("CRS:", mile_markers.crs)