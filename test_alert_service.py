from src.backend.alert_service import process_alert_request


result = process_alert_request(
    aoi_name="loudoun",
    species_name="bald_eagle",
    lookback_hours=72
)

print(result)