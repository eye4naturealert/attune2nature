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

    }

}

#--------------------------------------------------
#Helper Functions
#--------------------------------------------------

def list_aois():
    pass
  
def get_aoi():
    pass
  
def load_geometry():
    pass
  
def load_mile_markers():
    pass
        
#--------------------------------------------------
#Test Section
#--------------------------------------------------

if __name__ == "__main__":
    pass
