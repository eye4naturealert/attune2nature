# ============================================================
# EyeForNature Prototype v3 (Daily Batch)
# ============================================================

import requests
import geopandas as gpd
import pandas as pd

from shapely.geometry import Point
from datetime import datetime, timedelta, timezone

import sys
import io

import smtplib
from email.mime.text import MIMEText
import os

# ============================================================
# OUTPUT CAPTURE (ADD THIS WRAPPER)
# ============================================================

output_buffer = io.StringIO()
sys.stdout = output_buffer

# ============================================================
# CONFIG
# ============================================================

SEARCH_AREA_GEOJSON = "data/LoudonCounty.geojson"
AOI_GEOJSON = "data/LoudonCounty.geojson"

SPECIES = {
    "Eastern Box Turtle": 39814,
    "Common Snapping Turtle": 39672,
    "American Black Bear": 41638
}

LOOKBACK_HOURS = 72

url = "https://api.inaturalist.org/v1/observations"

headers = {
    "User-Agent": "Attune2Nature/1.0"
}

grand_total = 0
species_counts = {}
all_matches = []

EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
TO_EMAIL = "curranrunz@yahoo.com"

# ============================================================
# LOAD AOI
# ============================================================

print("=" * 70)
print("LOADING AOI")
print("=" * 70)

aoi = gpd.read_file(AOI_GEOJSON)
aoi = aoi.set_crs("EPSG:4326") if aoi.crs is None else aoi.to_crs("EPSG:4326")
polygon = aoi.union_all()

print("AOI Loaded")

# ============================================================
# TIME WINDOW
# ============================================================

utc_now = datetime.now(timezone.utc)
utc_start = utc_now - timedelta(hours=LOOKBACK_HOURS)
created_after = utc_start.replace(microsecond=0).isoformat()

print("=" * 70)
print(f"TIME WINDOW ({LOOKBACK_HOURS} HOURS)")
print("=" * 70)
print(f"Since: {created_after}")

# ============================================================
# MAIN LOOP (PER SPECIES)
# ============================================================

print("\n" + "=" * 70)
print("QUERYING INATURALIST")
print("=" * 70)

for species_name, taxon_id in SPECIES.items():

    print("\n" + "=" * 70)
    print(f"SPECIES: {species_name}")
    print("=" * 70)

    # --------------------------------------------------------
    # RESET PER SPECIES (CRITICAL)
    # --------------------------------------------------------
    all_observations = []
    matches = []

    page = 1
    per_page = 200

    # ========================================================
    # API PAGINATION
    # ========================================================

    while True:

        params = {
            "taxon_id": taxon_id,
            "created_d1": created_after,
            "swlat": aoi.total_bounds[1],
            "swlng": aoi.total_bounds[0],
            "nelat": aoi.total_bounds[3],
            "nelng": aoi.total_bounds[2],
            "per_page": per_page,
            "page": page
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=60)
            response.raise_for_status()

            data = response.json()
            batch = data.get("results", [])

            if not batch:
                break

            all_observations.extend(batch)

            print(f"Page {page}: {len(batch)} results")

            if len(batch) < per_page:
                break

            page += 1

        except Exception as e:
            print(f"API error: {e}")
            break

    print(f"Total downloaded: {len(all_observations)}")

    # ========================================================
    # AOI FILTERING
    # ========================================================

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

            quality = obs.get("quality_grade", "unknown")

            if quality == "needs_id":
                priority = 1
            elif quality == "research":
                priority = 2
            else:
                priority = 3

            matches.append({
                "species": species_name,
                "id": obs["id"],
                "observed_on": obs.get("observed_on", "Unknown"),
                "created_at": obs.get("created_at", "Unknown"),
                "observer": obs.get("user", {}).get("login", "Unknown"),
                "quality_grade": quality,
                "priority": priority,
                "lat": lat,
                "lon": lon,
                "url": f"https://www.inaturalist.org/observations/{obs['id']}"
            })

    # ========================================================
    # OUTPUT (PER SPECIES - FIXED SCOPE)
    # ========================================================

    matches.sort(key=lambda x: x["priority"])

    count = len(matches)
    species_counts[species_name] = count
    grand_total += count
    all_matches.extend(matches)

    print(f"\nMATCHES IN AOI: {count}")

    for i, obs in enumerate(matches, start=1):

        print("\n" + "-" * 60)
        print(f"Observation #{i}")
        print(f"Observer: {obs['observer']}")
        print(f"Observed: {obs['observed_on']}")
        print(f"Uploaded: {obs['created_at']}")
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

# ============================================================
# EXPORT CSV (SINGLE CLEAN BLOCK)
# ============================================================

if all_matches:

    df = pd.DataFrame(all_matches)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"observations_{timestamp}.csv"

    df.to_csv(filename, index=False)

    print("\nCSV exported:")
    print(filename)

else:
    print("\nNo observations to export.")

print("\nFinished.")

# ============================================================
# RESTORE CONSOLE + EXTRACT OUTPUT
# ============================================================

sys.stdout = sys.__stdout__

results_text = output_buffer.getvalue()

print("EMAIL OUTPUT LENGTH:", len(results_text))

# ============================================================
# EMAIL RESULTS
# ============================================================

msg = MIMEText(results_text)

msg["Subject"] = "Attune2Nature Daily Run Results"
msg["From"] = EMAIL_ADDRESS
msg["To"] = TO_EMAIL

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)

print("Email sent successfully.")
