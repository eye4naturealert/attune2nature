# --------------------------------------------------
# Imports
# --------------------------------------------------

import json
import sqlite3

from datetime import datetime, timezone
from pathlib import Path


# --------------------------------------------------
# Database Location
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_DIR = BASE_DIR / "instance"
DATABASE_PATH = DATABASE_DIR / "subscriptions.db"


# --------------------------------------------------
# Initialize Database
# --------------------------------------------------

def initialize_database():

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with sqlite3.connect(DATABASE_PATH) as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                email TEXT NOT NULL,

                aoi_name TEXT NOT NULL,

                species_json TEXT NOT NULL,

                time_interval TEXT NOT NULL,

                status TEXT NOT NULL
                    DEFAULT 'pending_verification',

                created_at TEXT NOT NULL,

                UNIQUE(email, aoi_name, time_interval)

            )
        """)

        connection.commit()


# --------------------------------------------------
# Save Subscription
# --------------------------------------------------

def save_subscription(
    email: str,
    aoi_name: str,
    species_names: list,
    time_interval: str
) -> dict:

    initialize_database()

    email = email.strip().lower()

    species_names = list(dict.fromkeys(species_names))

    species_json = json.dumps(species_names)

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    with sqlite3.connect(DATABASE_PATH) as connection:

        existing = connection.execute(
            """
            SELECT id, species_json, status
            FROM subscriptions
            WHERE email = ?
              AND aoi_name = ?
              AND time_interval = ?
            """,
            (email, aoi_name, time_interval)
        ).fetchone()

        if existing:

            subscription_id = existing[0]

            if (
                existing[1] == species_json
                and existing[2] == "pending_verification"
            ):
                return {
                    "id": subscription_id,
                    "status": "pending_verification",
                    "action": "already_exists"
                }

            connection.execute(
                """
                UPDATE subscriptions
                SET species_json = ?,
                    status = 'pending_verification'
                WHERE id = ?
                """,
                (species_json, subscription_id)
            )

            action = "updated"

        else:

            cursor = connection.execute(
                """
                INSERT INTO subscriptions (
                    email,
                    aoi_name,
                    species_json,
                    time_interval,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    email,
                    aoi_name,
                    species_json,
                    time_interval,
                    "pending_verification",
                    created_at
                )
            )

            subscription_id = cursor.lastrowid

            action = "created"

        connection.commit()

    return {
        "id": subscription_id,
        "status": "pending_verification",
        "action": action
    }


# --------------------------------------------------
# Retrieve Subscriptions
# --------------------------------------------------

def get_subscriptions():

    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as connection:

        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                id,
                email,
                aoi_name,
                species_json,
                time_interval,
                status,
                created_at

            FROM subscriptions

            ORDER BY created_at DESC
            """
        ).fetchall()

    subscriptions = []

    for row in rows:

        subscription = dict(row)

        subscription["species"] = json.loads(
            subscription.pop("species_json")
        )

        subscriptions.append(subscription)

    return subscriptions