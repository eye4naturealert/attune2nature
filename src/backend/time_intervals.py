# --------------------------------------------------
# Time Interval Registry
# --------------------------------------------------

TIME_INTERVALS = {
    "24_hours": {
        "label": "Last 24 Hours",
        "hours": 24
    },

    "3_days": {
        "label": "Last 3 Days",
        "hours": 72
    },

    "1_week": {
        "label": "Last 7 Days",
        "hours": 168
    },

    "1_month": {
        "label": "Last 30 Days",
        "hours": 720
    }
}
# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def get_time_interval_options() -> list:

    options = []

    for key, interval in TIME_INTERVALS.items():
        options.append({
            "value": key,
            "label": interval["label"]
        })

    return options