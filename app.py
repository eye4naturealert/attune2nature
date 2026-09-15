import json

from flask import Flask, render_template, request, jsonify

from src.backend.alert_service import (
    get_alert_options,
    process_alert_request
)

from src.spatial.aoi_registry import AOIS


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():

    options = get_alert_options()
    result = None

    if request.method == "POST":

        aoi_name = request.form["aoi"]
        species_name = request.form["species"]
        time_interval = request.form["time_interval"]

        result = process_alert_request(
            aoi_name=aoi_name,
            species_name=species_name,
            time_interval=time_interval
        )

    return render_template(
        "index.html",
        options=options,
        result=result
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

    with open(geojson_path, "r", encoding="utf-8") as file:
        geojson_data = json.load(file)

    return jsonify(geojson_data)


if __name__ == "__main__":
    app.run(debug=True)