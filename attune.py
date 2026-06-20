# ============================================================
# EyeForNature Prototype v3 (Daily Batch)
#
# PURPOSE:
#   Run once per day (e.g., 6am EST via scheduler)
#   Pull last 24 hours of iNaturalist observations
#   Filter by AOI
# ============================================================


import requests
import geopandas as gpd

from shapely.geometry import Point
from datetime import datetime, timedelta, timezone

# ============================================================
# INPUT FILES
# ============================================================

SEARCH_AREA_GEOJSON = r"C:\Users\curra\OneDrive\Documents\Projects\Eye4Nature\Data/LoudonCounty.geojson"
AOI_GEOJSON = r"C:\Users\curra\OneDrive\Documents\Projects\Eye4Nature\Data/LoudonCounty.geojson"


# ============================================================
# SPECIES MONITOR LIST
# ============================================================

SPECIES = {
    "Eastern Box Turtle": 39814,
    "Common Snapping Turtle": 39672,
    "American Black Bear": 41639
}


# ============================================================
# LOAD SEARCH AREA (BOUNDING BOX)
# ============================================================

print("=" * 70)
print("LOADING SEARCH AREA")
print("=" * 70)

search_area = gpd.read_file(SEARCH_AREA_GEOJSON)

search_area = search_area.set_crs("EPSG:4326") if search_area.crs is None else search_area.to_crs("EPSG:4326")

west, south, east, north = search_area.total_bounds

print(f"Bounding Box → W:{west}, S:{south}, E:{east}, N:{north}")


# ============================================================
# LOAD AOI (POLYGON FILTER)
# ============================================================

print("\n" + "=" * 70)
print("LOADING AOI")
print("=" * 70)

aoi = gpd.read_file(AOI_GEOJSON)

aoi = aoi.set_crs("EPSG:4326") if aoi.crs is None else aoi.to_crs("EPSG:4326")

polygon = aoi.union_all()

print("AOI Loaded")


# ============================================================
# TIME WINDOW (LAST 24 HOURS, UTC)
# ============================================================

utc_now = datetime.now(timezone.utc)
utc_24hrs_ago = utc_now - timedelta(hours=24)

created_after = utc_24hrs_ago.replace(microsecond=0).isoformat()

print("\n" + "=" * 70)
print("TIME WINDOW (24 HOURS)")
print("=" * 70)
print(f"Now (UTC): {utc_now}")
print(f"Since   : {created_after}")


# ============================================================
# API Configuration
# ============================================================

url = "https://api.inaturalist.org/v1/observations"

headers = {
    "User-Agent": "Attune2Nature/1.0"
}

# ============================================================
# Tracking Variables
# ============================================================

grand_total = 0
species_counts = {}


# ============================================================
# MAIN LOOP
# ============================================================

print("\n" + "=" * 70)
print("QUERYING INATURALIST")
print("=" * 70)


for species_name, taxon_id in SPECIES.items():

    print("\n" + "=" * 70)
    print(f"SPECIES: {species_name}")
    print("=" * 70)

    page = 1
    per_page = 200

    all_observations = []

    # ========================================================
    # PAGINATION LOOP (ROBUST)
    # ========================================================

    while True:

        params = {
            "taxon_id": taxon_id,
            "created_d1": created_after,
            "swlat": south,
            "swlng": west,
            "nelat": north,
            "nelng": east,
            "per_page": per_page,
            "page": page
        }

        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()
            batch = data.get("results", [])
            total_results = data.get("total_results", None)

            if not batch:
                break

            all_observations.extend(batch)

            print(f"Page {page}: {len(batch)} results (total so far: {len(all_observations)})")

            # STOP CONDITIONS
            if total_results and len(all_observations) >= total_results:
                break

            if len(batch) < per_page:
                break

            page += 1

        except Exception as e:
            print(f"API error on page {page}: {e}")
            all_observations = []
            break


    print(f"Total downloaded: {len(all_observations)}")


    # ========================================================
    # AOI FILTERING
    # ========================================================

    matches = []

    for obs in all_observations:

        geojson = obs.get("geojson")
        if not geojson or "coordinates" not in geojson:
            continue

        coords = geojson["coordinates"]
        if not coords or len(coords) != 2:
            continue

        lon, lat = coords

        point = Point(lon, lat)

        if point.within(polygon):

            matches.append({
                "id": obs["id"],
                "date": obs.get("observed_on", "Unknown"),
                "observer": obs.get("user", {}).get("login", "Unknown"),
                "quality_grade": obs.get("quality_grade", "unknown"),
                "lat": lat,
                "lon": lon,
                "url": f"https://www.inaturalist.org/observations/{obs['id']}"
            })


    # ========================================================
    # OUTPUT
    # ========================================================

    count = len(matches)
    species_counts[species_name] = count
    grand_total += count

    print(f"\nMATCHES IN AOI: {count}")

    for i, obs in enumerate(matches, start=1):

        print("\n" + "-" * 60)
        print(f"Observation #{i}")
        print(f"Observer: {obs['observer']}")
        print(f"Date: {obs['date']}")
        print(f"Quality: {obs['quality_grade']}")
        print(f"Coords: {obs['lat']:.5f}, {obs['lon']:.5f}")
        print(f"URL: {obs['url']}")


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("DAILY SUMMARY")
print("=" * 70)

for species, count in species_counts.items():
    print(f"{species}: {count}")

print("\n" + "-" * 70)
print(f"TOTAL OBSERVATIONS: {grand_total}")
print("\nFinished.")
