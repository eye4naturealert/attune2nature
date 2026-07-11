#--------------------------------------------------
#Imports
#--------------------------------------------------

from pathlib import Path
import geopandas as gpd

#--------------------------------------------------
#Project Root (pathlib)
#--------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

#--------------------------------------------------
#AOI Registry Dictionary
#--------------------------------------------------
AOIS = {

    "wod": {

        "name": "Washington & Old Dominion Trail",

        "geometry": BASE_DIR / "data" / "aois" / "OSM_W&OD_Trail_25mBuffer.geojson",

        "reference_layers": {

            "mile_markers":
                BASE_DIR / "data" / "reference" / "WOD_MileMarkers.geojson"

        }

    },

    "loudoun": {

        "name": "Loudoun County",

        "geometry":
            BASE_DIR / "data" / "aois" / "LoudounCounty.geojson",

        "reference_layers": {}

    },

    "fairfax": {

        "name": "Fairfax County",

        "geometry":
            BASE_DIR / "data" / "aois" / "FairfaxCounty.geojson",

        "reference_layers": {}

    },

    "arlington": {

        "name": "Arlington County",

        "geometry":
            BASE_DIR / "data" / "aois" / "ArlingtonCounty.geojson",

        "reference_layers": {}

    },

    "falls_church": {

        "name": "Falls Church City",

        "geometry":
            BASE_DIR / "data" / "aois" / "FallsChurchCity.geojson",

        "reference_layers": {}

    },

    "alexandria": {

        "name": "Alexandria City",

        "geometry":
            BASE_DIR / "data" / "aois" / "AlexandriaCity.geojson",

        "reference_layers": {}

    }

}

#--------------------------------------------------
#Helper Functions
#--------------------------------------------------

def list_aois():
    return list(AOIS.keys())
  
def get_aoi(name):
    return AOIS.get(name)
  
def load_geometry(name):

    aoi = get_aoi(name)

    if aoi is None:
        raise ValueError(f"Unknown AOI: {name}")

    return gpd.read_file(aoi["geometry"])
  
def load_mile_markers():
    pass
        
#--------------------------------------------------
#Test Section
#--------------------------------------------------

#--------------------------------------------------
#Test Section
#--------------------------------------------------

if __name__ == "__main__":

    print("Project Root:")
    print(BASE_DIR)

    print("\nAvailable AOIs:")
    print(list_aois())

    print("\nTesting get_aoi:")
    print(get_aoi("loudoun"))

    print("\nAOI Files:")

    for key, aoi in AOIS.items():
        print(key)
        print(aoi["geometry"])
        print("Exists:", aoi["geometry"].exists())
        print()

print("\nTesting geometry loading:")

for aoi_name in list_aois():

    print(f"\nLoading: {aoi_name}")

    gdf = load_geometry(aoi_name)

    print("Rows:", len(gdf))
    print("CRS:", gdf.crs)
    print("Geometry type:", gdf.geometry.geom_type.iloc[0])