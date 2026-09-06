# --------------------------------------------------
# Imports
# --------------------------------------------------

from flask import Flask, render_template

from src.backend.alert_service import get_alert_options


# --------------------------------------------------
# Flask App
# --------------------------------------------------

app = Flask(__name__)


# --------------------------------------------------
# Home Page
# --------------------------------------------------

@app.route("/")
def home():

    options = get_alert_options()

    return render_template(
        "index.html",
        options=options
    )


# --------------------------------------------------
# Run App
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)