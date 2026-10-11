# --------------------------------------------------
# Imports
# --------------------------------------------------

import os
import smtplib

from email.message import EmailMessage


# --------------------------------------------------
# Send Email
# --------------------------------------------------

def send_email(recipient, subject, body):

    email_address = os.environ.get("EMAIL_ADDRESS")
    email_password = os.environ.get("EMAIL_PASSWORD")

    if not email_address or not email_password:

        raise RuntimeError(
            "EMAIL_ADDRESS and EMAIL_PASSWORD "
            "environment variables must be configured."
        )

    msg = EmailMessage()

    msg["From"] = email_address
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.set_content(body)

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        timeout=30
    ) as server:

        server.login(
            email_address,
            email_password
        )

        server.send_message(msg)


# --------------------------------------------------
# Verification Email
# --------------------------------------------------

def send_verification_email(recipient, verification_url):

    subject = "Verify Your Attune2Nature Wildlife Alert"

    body = f"""
Welcome to Attune2Nature!

Please verify your email address to activate
your wildlife alert subscription.

Click the link below:

{verification_url}

This verification link expires in 24 hours.

If you did not request this subscription,
you can ignore this email.

Attune2Nature
Wildlife alerts powered by iNaturalist observations
"""

    send_email(recipient, subject, body)


# --------------------------------------------------
# Activation Confirmation Email
# --------------------------------------------------

def send_activation_email(recipient, unsubscribe_url):

    subject = "Your Attune2Nature Subscription Is Active"

    body = f"""
Your Attune2Nature subscription is now active!

Your email address has been verified successfully.

Wildlife alert delivery is still under development,
so scheduled wildlife notifications are not yet enabled.

You can unsubscribe using the following link:

{unsubscribe_url}

Keep this email for future reference.

Attune2Nature
"""

    send_email(recipient, subject, body)