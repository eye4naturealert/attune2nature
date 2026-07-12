#--------------------------------------------------
# Imports
#--------------------------------------------------

from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
import sys
import time

import pandas as pd
import requests


#--------------------------------------------------
# Allow imports from the src folder
#--------------------------------------------------

SRC_DIR = Path(__file__).resolve().parents[1]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from spatial.aoi_registry import get_aoi
from species.species_registry import (
    get_species,
    list_active_species,
)


#--------------------------------------------------
# Project Paths
#--------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "audits"
)


#--------------------------------------------------
# User Settings
#--------------------------------------------------

# Choose the regional AOI used for the audit.
#
# Recommended:
# "loudoun"
# "fairfax"
# "arlington"
# "falls_church"
# "alexandria"

AOI_NAME = "loudoun"


# Number of days back from the current time.

LOOKBACK_DAYS = 365


# Maximum observations examined per species.
#
# iNaturalist allows up to 200 observations
# in one API response.

MAX_RECORDS_PER_SPECIES = 200


# Pause between requests to avoid sending
# requests too quickly.

REQUEST_DELAY_SECONDS = 1.0


# Preliminary threshold for deciding whether a
# species may support precise location alerts.
#
# This can be adjusted after reviewing the audit.

PRECISE_ALERT_PUBLIC_PERCENT = 80.0


# Require at least this many public observations
# before recommending precise alerts.

MIN_PUBLIC_OBSERVATIONS = 10


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
# Get AOI Place ID
#--------------------------------------------------

def get_aoi_place_id(
    aoi_name: str
) -> int:
    """
    Return the iNaturalist place ID for an AOI.
    """

    aoi = get_aoi(aoi_name)

    if aoi is None:
        raise ValueError(
            f"Unknown AOI '{aoi_name}'."
        )

    place_id = aoi.get(
        "inaturalist_place_id"
    )

    if place_id is None:
        raise ValueError(
            f"AOI '{aoi_name}' does not have an "
            f"iNaturalist place ID."
        )

    return int(place_id)


#--------------------------------------------------
# Build Start Date
#--------------------------------------------------

def get_created_after(
    lookback_days: int
) -> str:
    """
    Calculate the beginning of the audit period.
    """

    if lookback_days <= 0:
        raise ValueError(
            "LOOKBACK_DAYS must be greater than zero."
        )

    start_time = (
        datetime.now(timezone.utc)
        - timedelta(days=lookback_days)
    )

    return start_time.isoformat(
        timespec="seconds"
    )


#--------------------------------------------------
# Query One Species
#--------------------------------------------------

def query_species(
    place_id: int,
    taxon_id: int,
    created_after: str
) -> dict:
    """
    Retrieve one sample of observations for a species.
    """

    params = {

        "place_id": place_id,

        "taxon_id": taxon_id,

        "created_d1": created_after,

        "per_page": MAX_RECORDS_PER_SPECIES,

        "page": 1,

        "order_by": "created_at",

        "order": "desc"

    }

    try:

        response = requests.get(
            INATURALIST_URL,
            params=params,
            headers=HEADERS,
            timeout=60
        )

        response.raise_for_status()

    except requests.exceptions.Timeout as exc:

        raise RuntimeError(
            "The iNaturalist request timed out."
        ) from exc

    except requests.exceptions.HTTPError as exc:

        raise RuntimeError(
            "iNaturalist returned HTTP status "
            f"{exc.response.status_code}."
        ) from exc

    except requests.exceptions.RequestException as exc:

        raise RuntimeError(
            f"Could not connect to iNaturalist: {exc}"
        ) from exc

    return response.json()


#--------------------------------------------------
# Calculate Median Safely
#--------------------------------------------------

def calculate_median(
    values: list[float]
) -> float | None:
    """
    Return the median of a list or None when empty.
    """

    if not values:
        return None

    return round(
        float(median(values)),
        2
    )


#--------------------------------------------------
# Classify Alert Support
#--------------------------------------------------

def classify_alert_support(
    sampled_count: int,
    public_count: int,
    public_percent: float
) -> str:
    """
    Provide a preliminary alert-mode recommendation.
    """

    if sampled_count == 0:
        return "insufficient_data"

    if public_count == 0:
        return "regional_only"

    if (
        public_count
        >= MIN_PUBLIC_OBSERVATIONS
        and public_percent
        >= PRECISE_ALERT_PUBLIC_PERCENT
    ):
        return "precise_and_regional"

    return "mixed_review"


#--------------------------------------------------
# Analyze Species Results
#--------------------------------------------------

def analyze_species(
    species_key: str,
    response_data: dict,
    aoi_name: str,
    aoi_display_name: str
) -> dict:
    """
    Calculate audit statistics for one species.
    """

    species = get_species(
        species_key
    )

    observations = response_data.get(
        "results",
        []
    )

    total_results = response_data.get(
        "total_results",
        0
    )

    sampled_count = len(
        observations
    )

    obscured_observations = [
        observation
        for observation in observations
        if observation.get(
            "obscured",
            False
        )
    ]

    public_observations = [
        observation
        for observation in observations
        if not observation.get(
            "obscured",
            False
        )
    ]

    obscured_count = len(
        obscured_observations
    )

    public_count = len(
        public_observations
    )

    if sampled_count > 0:

        obscured_percent = round(
            (
                obscured_count
                / sampled_count
            )
            * 100,
            2
        )

        public_percent = round(
            (
                public_count
                / sampled_count
            )
            * 100,
            2
        )

    else:

        obscured_percent = 0.0
        public_percent = 0.0

    all_accuracy_values = [

        float(
            observation[
                "positional_accuracy"
            ]
        )

        for observation in observations

        if observation.get(
            "positional_accuracy"
        ) is not None

    ]

    public_accuracy_values = [

        float(
            observation[
                "positional_accuracy"
            ]
        )

        for observation in public_observations

        if observation.get(
            "positional_accuracy"
        ) is not None

    ]

    missing_accuracy_count = sum(

        observation.get(
            "positional_accuracy"
        ) is None

        for observation in observations

    )

    alert_support = classify_alert_support(
        sampled_count=sampled_count,
        public_count=public_count,
        public_percent=public_percent
    )

    return {

        "aoi_key":
            aoi_name,

        "aoi_name":
            aoi_display_name,

        "species_key":
            species_key,

        "common_name":
            species.get(
                "common_name"
            ),

        "scientific_name":
            species.get(
                "scientific_name"
            ),

        "taxon_id":
            species.get(
                "taxon_id"
            ),

        "group":
            species.get(
                "group"
            ),

        "subgroup":
            species.get(
                "subgroup"
            ),

        "lookback_days":
            LOOKBACK_DAYS,

        "total_results":
            total_results,

        "records_examined":
            sampled_count,

        "public_count":
            public_count,

        "public_percent":
            public_percent,

        "obscured_count":
            obscured_count,

        "obscured_percent":
            obscured_percent,

        "accuracy_reported_count":
            len(
                all_accuracy_values
            ),

        "accuracy_missing_count":
            missing_accuracy_count,

        "median_gps_accuracy_m":
            calculate_median(
                all_accuracy_values
            ),

        "public_accuracy_reported_count":
            len(
                public_accuracy_values
            ),

        "public_median_gps_accuracy_m":
            calculate_median(
                public_accuracy_values
            ),

        "alert_support":
            alert_support

    }


#--------------------------------------------------
# Print One Species Summary
#--------------------------------------------------

def print_species_summary(
    audit_result: dict
) -> None:
    """
    Print a concise summary for one species.
    """

    print(
        f"Total results       : "
        f"{audit_result['total_results']}"
    )

    print(
        f"Records examined    : "
        f"{audit_result['records_examined']}"
    )

    print(
        f"Public              : "
        f"{audit_result['public_count']} "
        f"({audit_result['public_percent']}%)"
    )

    print(
        f"Obscured            : "
        f"{audit_result['obscured_count']} "
        f"({audit_result['obscured_percent']}%)"
    )

    print(
        f"Median GPS accuracy : "
        f"{audit_result['median_gps_accuracy_m']} m"
    )

    print(
        f"Alert support       : "
        f"{audit_result['alert_support']}"
    )


#--------------------------------------------------
# Run Full Species Audit
#--------------------------------------------------

def run_species_audit(
    aoi_name: str
) -> pd.DataFrame:
    """
    Audit every active species in the registry.
    """

    aoi = get_aoi(
        aoi_name
    )

    if aoi is None:
        raise ValueError(
            f"Unknown AOI '{aoi_name}'."
        )

    place_id = get_aoi_place_id(
        aoi_name
    )

    created_after = get_created_after(
        LOOKBACK_DAYS
    )

    species_keys = list_active_species()

    audit_rows = []

    print("\n" + "=" * 90)
    print("ATTUNE2NATURE SPECIES AUDIT")
    print("=" * 90)

    print(
        f"AOI              : "
        f"{aoi['name']}"
    )

    print(
        f"iNaturalist ID   : "
        f"{place_id}"
    )

    print(
        f"Lookback         : "
        f"{LOOKBACK_DAYS} days"
    )

    print(
        f"Species to audit : "
        f"{len(species_keys)}"
    )

    for index, species_key in enumerate(
        species_keys,
        start=1
    ):

        species = get_species(
            species_key
        )

        print("\n" + "-" * 90)

        print(
            f"[{index}/{len(species_keys)}] "
            f"{species['common_name']}"
        )

        print(
            f"Taxon ID: "
            f"{species['taxon_id']}"
        )

        try:

            response_data = query_species(
                place_id=place_id,
                taxon_id=species[
                    "taxon_id"
                ],
                created_after=created_after
            )

            audit_result = analyze_species(
                species_key=species_key,
                response_data=response_data,
                aoi_name=aoi_name,
                aoi_display_name=aoi[
                    "name"
                ]
            )

        except Exception as exc:

            print(
                f"Audit failed: {exc}"
            )

            audit_result = {

                "aoi_key":
                    aoi_name,

                "aoi_name":
                    aoi["name"],

                "species_key":
                    species_key,

                "common_name":
                    species.get(
                        "common_name"
                    ),

                "scientific_name":
                    species.get(
                        "scientific_name"
                    ),

                "taxon_id":
                    species.get(
                        "taxon_id"
                    ),

                "group":
                    species.get(
                        "group"
                    ),

                "subgroup":
                    species.get(
                        "subgroup"
                    ),

                "lookback_days":
                    LOOKBACK_DAYS,

                "total_results":
                    None,

                "records_examined":
                    0,

                "public_count":
                    0,

                "public_percent":
                    0.0,

                "obscured_count":
                    0,

                "obscured_percent":
                    0.0,

                "accuracy_reported_count":
                    0,

                "accuracy_missing_count":
                    0,

                "median_gps_accuracy_m":
                    None,

                "public_accuracy_reported_count":
                    0,

                "public_median_gps_accuracy_m":
                    None,

                "alert_support":
                    "query_error",

                "error":
                    str(exc)

            }

        audit_rows.append(
            audit_result
        )

        print_species_summary(
            audit_result
        )

        if index < len(species_keys):

            time.sleep(
                REQUEST_DELAY_SECONDS
            )

    return pd.DataFrame(
        audit_rows
    )


#--------------------------------------------------
# Export Audit
#--------------------------------------------------

def export_audit(
    audit_df: pd.DataFrame,
    aoi_name: str
) -> Path:
    """
    Export the species audit to CSV.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_path = (
        OUTPUT_DIR
        / (
            f"species_audit_"
            f"{aoi_name}_"
            f"{timestamp}.csv"
        )
    )

    audit_df.to_csv(
        output_path,
        index=False
    )

    return output_path


#--------------------------------------------------
# Test / Run Section
#--------------------------------------------------

if __name__ == "__main__":

    audit_df = run_species_audit(
        AOI_NAME
    )

    audit_df = audit_df.sort_values(
        by=[
            "group",
            "subgroup",
            "common_name"
        ],
        na_position="last"
    )

    print("\n" + "=" * 90)
    print("FINAL AUDIT SUMMARY")
    print("=" * 90)

    summary_columns = [

        "common_name",

        "group",

        "subgroup",

        "total_results",

        "records_examined",

        "public_percent",

        "obscured_percent",

        "public_median_gps_accuracy_m",

        "alert_support"

    ]

    print(
        audit_df[
            summary_columns
        ].to_string(
            index=False
        )
    )

    output_path = export_audit(
        audit_df=audit_df,
        aoi_name=AOI_NAME
    )

    print("\nAudit exported:")
    print(output_path)