from src.backend.alert_service import process_alert_request


result = process_alert_request(
    aoi_name="loudoun",
    species_name="eastern_box_turtle",
    time_interval="1_month"
)


print("\nALERT SUMMARY")
print("=" * 60)

print("AOI:", result["aoi_name"])
print("Species:", result["common_name"])
print("Time Interval:", result["time_interval_label"])
print("Observation Count:", result["observation_count"])


print("\nMATCHING OBSERVATIONS")
print("=" * 60)

for obs in result["observations"]:

    print("\nObservation ID:", obs["observation_id"])
    print("Observed On:", obs["observed_on"])
    print("Observer:", obs["observer"])
    print("Quality Grade:", obs["quality_grade"])
    print("Geoprivacy:", obs["geoprivacy"])
    print("Taxon Geoprivacy:", obs["taxon_geoprivacy"])
    print("Latitude:", obs["latitude"])
    print("Longitude:", obs["longitude"])
    print("URL:", obs["url"])