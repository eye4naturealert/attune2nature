import json
import re

from flask import Flask, render_template, request, jsonify

from src.backend.alert_service import get_alert_options
from src.spatial.aoi_registry import AOIS


app = Flask(__name__)


# --------------------------------------------------
# Homepage / Subscription Form
# --------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def home():

    options = get_alert_options()

    errors = []
    confirmation = None

    form_data = {
        "aoi": "",
        "species": [],
        "time_interval": "",
        "email": ""
    }

    if request.method == "POST":

        form_data = {
            "aoi": request.form.get("aoi", "").strip(),
            "species": request.form.getlist("species"),
            "time_interval": request.form.get(
                "time_interval", ""
            ).strip(),
            "email": request.form.get(
                "email", ""
            ).strip()
        }

        # ------------------------------------------
        # Validate AOI
        # ------------------------------------------

        valid_aois = {
            item["value"]
            for item in options["aois"]
        }

        if form_data["aoi"] not in valid_aois:
            errors.append("Please select a valid area.")

        # ------------------------------------------
        # Validate Species
        # ------------------------------------------

        valid_species = {
            item["value"]
            for item in options["species"]
        }

        selected_species = list(
            dict.fromkeys(form_data["species"])
        )

        if not selected_species:
            errors.append(
                "Please select at least one species."
            )

        elif any(
            species not in valid_species
            for species in selected_species
        ):
            errors.append(
                "One or more selected species are invalid."
            )

        # ------------------------------------------
        # Validate Alert Interval
        # ------------------------------------------

        valid_intervals = {
            item["value"]
            for item in options["time_intervals"]
        }

        if form_data["time_interval"] not in valid_intervals:
            errors.append(
                "Please select a valid alert interval."
            )

        # ------------------------------------------
        # Validate Email
        # ------------------------------------------

        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.fullmatch(
            email_pattern,
            form_data["email"]
        ):
            errors.append(
                "Please enter a valid email address."
            )

        # ------------------------------------------
        # Prepare Subscription Preview
        # ------------------------------------------

        if not errors:

            species_labels = {
                item["value"]: item["label"]
                for item in options["species"]
            }

            aoi_labels = {
                item["value"]: item["label"]
                for item in options["aois"]
            }

            interval_labels = {
                item["value"]: item["label"]
                for item in options["time_intervals"]
            }

            confirmation = {
                "aoi": aoi_labels[form_data["aoi"]],
                "species": [
                    species_labels[name]
                    for name in selected_species
                ],
                "time_interval": interval_labels[
                    form_data["time_interval"]
                ],
                "email": form_data["email"]
            }

    return render_template(
        "index.html",
        options=options,
        errors=errors,
        confirmation=confirmation,
        form_data=form_data
    )


# --------------------------------------------------
# AOI GeoJSON
# --------------------------------------------------

@app.route("/aoi/<aoi_name>/geojson")
def get_aoi_geojson(aoi_name):

    if aoi_name not in AOIS:
        return jsonify({
            "error": "AOI not found"
        }), 404

    geojson_path = AOIS[aoi_name]["geometry"]

    try:
        with open(
            geojson_path,
            "r",
            encoding="utf-8"
        ) as file:
            geojson_data = json.load(file)

    except (OSError, json.JSONDecodeError):
        return jsonify({
            "error": "Unable to load AOI geometry"
        }), 500

    return jsonify(geojson_data)


if __name__ == "__main__":
    app.run(debug=True)