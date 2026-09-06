# --------------------------------------------------
# Imports
# --------------------------------------------------

from flask import Flask, render_template, request

from src.backend.alert_service import get_alert_options

from src.backend.alert_service import (
    get_alert_options,
    process_alert_request
)

# --------------------------------------------------
# Flask App
# --------------------------------------------------

app = Flask(__name__)


# --------------------------------------------------
# Home Page
# --------------------------------------------------

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
# Run App
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)