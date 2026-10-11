# --------------------------------------------------
# Imports
# --------------------------------------------------

import json
import re
import smtplib

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    url_for
)

from src.backend.alert_service import get_alert_options

from src.backend.subscription_service import (
    create_pending_subscription,
    verify_subscription,
    unsubscribe
)

from src.backend.email_service import (
    send_verification_email,
    send_activation_email
)

from src.spatial.aoi_registry import AOIS


app = Flask(__name__)


# --------------------------------------------------
# Homepage
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

        valid_aois = {
            item["value"]
            for item in options["aois"]
        }

        valid_species = {
            item["value"]
            for item in options["species"]
        }

        valid_intervals = {
            item["value"]
            for item in options["time_intervals"]
        }

        selected_species = list(
            dict.fromkeys(form_data["species"])
        )

        if form_data["aoi"] not in valid_aois:
            errors.append("Please select a valid area.")

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

        if form_data["time_interval"] not in valid_intervals:
            errors.append(
                "Please select a valid alert interval."
            )

        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.fullmatch(
            email_pattern,
            form_data["email"]
        ):
            errors.append(
                "Please enter a valid email address."
            )

        # ------------------------------------------
        # Save Pending Subscription
        # ------------------------------------------

        if not errors:

            try:

                subscription = create_pending_subscription(
                    email=form_data["email"],
                    aoi_name=form_data["aoi"],
                    species_names=selected_species,
                    time_interval=form_data["time_interval"]
                )

                action = subscription["action"]

                if action == "existing_active":

                    # Do not disclose whether the
                    # submitted address has an active
                    # subscription.

                    confirmation = {
                        "message": (
                            "If this request is eligible, "
                            "a verification email will be sent."
                        )
                    }

                else:

                    token = subscription["verification_token"]

                    verification_url = url_for(
                        "verify_email",
                        token=token,
                        _external=True
                    )

                    send_verification_email(
                        recipient=form_data["email"],
                        verification_url=verification_url
                    )

                    confirmation = {
                        "message": (
                            "A verification email has been "
                            "sent. Check your inbox and "
                            "click the link to activate "
                            "your subscription."
                        )
                    }

            except (
                OSError,
                smtplib.SMTPException,
                RuntimeError
            ):

                errors.append(
                    "Your request was saved, but the "
                    "verification email could not be sent. "
                    "Please try submitting the form again."
                )

    return render_template(
        "index.html",
        options=options,
        errors=errors,
        confirmation=confirmation,
        form_data=form_data
    )


# --------------------------------------------------
# Verify Email
# --------------------------------------------------

# --------------------------------------------------
# Verify Email
# --------------------------------------------------

@app.route("/verify/<token>")
def verify_email(token):

    result = verify_subscription(token)

    if not result["success"]:

        return render_template(
            "subscription_status.html",
            title="Verification Failed",
            message=result["message"]
        ), 400

    unsubscribe_url = url_for(
        "unsubscribe_email",
        token=result["unsubscribe_token"],
        _external=True
    )

    try:

        send_activation_email(
            recipient=result["email"],
            unsubscribe_url=unsubscribe_url
        )

        message = (
            "Your email address has been verified. "
            "Your subscription is active. "
            "Check your inbox for your confirmation "
            "and unsubscribe link."
        )

    except (
        OSError,
        smtplib.SMTPException,
        RuntimeError
    ):

        return render_template(
            "subscription_status.html",
            title="Email Verified!",
            message=(
                "Your subscription is active, "
                "but the confirmation email could "
                "not be delivered. Save the "
                "unsubscribe link below."
            ),
            recovery_unsubscribe_url=unsubscribe_url
        )

    return render_template(
        "subscription_status.html",
        title="Email Verified!",
        message=message
    )

# --------------------------------------------------
# Unsubscribe
# --------------------------------------------------

@app.route(
    "/unsubscribe/<token>",
    methods=["GET", "POST"]
)
def unsubscribe_email(token):

    if request.method == "GET":

        return render_template(
            "unsubscribe.html",
            token=token
        )

    success = unsubscribe(token)

    if success:

        title = "Unsubscribed"
        message = (
            "Your wildlife alert subscription "
            "has been deactivated."
        )

    else:

        title = "Unable to Unsubscribe"
        message = (
            "This unsubscribe link is invalid "
            "or has already been used."
        )

    return render_template(
        "subscription_status.html",
        title=title,
        message=message
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