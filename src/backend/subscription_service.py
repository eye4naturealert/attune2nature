# --------------------------------------------------
# Imports
# --------------------------------------------------

import hashlib
import json
import secrets
import sqlite3

from datetime import datetime, timedelta, timezone
from pathlib import Path


# --------------------------------------------------
# Database Location
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_DIR = BASE_DIR / "instance"
DATABASE_PATH = DATABASE_DIR / "subscriptions.db"

TOKEN_LIFETIME_HOURS = 24


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc)


def hash_token(token):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def database_connection():

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


# --------------------------------------------------
# Initialize / Upgrade Database
# --------------------------------------------------

def initialize_database():

    with database_connection() as connection:

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

        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(subscriptions)"
            )
        }

        new_columns = {
            "verification_token_hash": "TEXT",
            "verification_expires_at": "TEXT",
            "unsubscribe_token_hash": "TEXT",
            "verified_at": "TEXT",
            "unsubscribed_at": "TEXT",
            "last_checked_at": "TEXT"
        }

        for column, column_type in new_columns.items():

            if column not in columns:

                connection.execute(
                    f"ALTER TABLE subscriptions "
                    f"ADD COLUMN {column} {column_type}"
                )

        connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_verification_token
            ON subscriptions(verification_token_hash)
        """)

        connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_unsubscribe_token
            ON subscriptions(unsubscribe_token_hash)
        """)

        connection.commit()


# --------------------------------------------------
# Create Pending Subscription
# --------------------------------------------------

def create_pending_subscription(
    email,
    aoi_name,
    species_names,
    time_interval
):

    initialize_database()

    email = email.strip().lower()

    species_names = list(
        dict.fromkeys(species_names)
    )

    species_json = json.dumps(species_names)

    verification_token = secrets.token_urlsafe(32)

    verification_hash = hash_token(
        verification_token
    )

    now = utc_now()

    expires_at = (
        now + timedelta(hours=TOKEN_LIFETIME_HOURS)
    ).isoformat()

    with database_connection() as connection:

        # Use an immediate transaction so the
        # active-subscription check and write are atomic.

        connection.execute("BEGIN IMMEDIATE")

        existing = connection.execute(
            """
            SELECT id, status
            FROM subscriptions
            WHERE email = ?
              AND aoi_name = ?
              AND time_interval = ?
            """,
            (email, aoi_name, time_interval)
        ).fetchone()

        if existing and existing["status"] == "active":

            connection.commit()

            return {
                "action": "existing_active",
                "verification_token": None
            }

        if existing:

            subscription_id = existing["id"]

            connection.execute(
                """
                UPDATE subscriptions

                SET species_json = ?,
                    status = 'pending_verification',
                    verification_token_hash = ?,
                    verification_expires_at = ?,
                    unsubscribe_token_hash = NULL,
                    verified_at = NULL,
                    unsubscribed_at = NULL

                WHERE id = ?
                """,
                (
                    species_json,
                    verification_hash,
                    expires_at,
                    subscription_id
                )
            )

            action = "updated_pending"

        else:

            cursor = connection.execute(
                """
                INSERT INTO subscriptions (
                    email,
                    aoi_name,
                    species_json,
                    time_interval,
                    status,
                    created_at,
                    verification_token_hash,
                    verification_expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    email,
                    aoi_name,
                    species_json,
                    time_interval,
                    "pending_verification",
                    now.isoformat(),
                    verification_hash,
                    expires_at
                )
            )

            subscription_id = cursor.lastrowid

            action = "created"

        connection.commit()

    return {
        "action": action,
        "id": subscription_id,
        "verification_token": verification_token
    }


# --------------------------------------------------
# Verify Subscription
# --------------------------------------------------

def verify_subscription(token):

    initialize_database()

    token_hash = hash_token(token)

    with database_connection() as connection:

        connection.execute("BEGIN IMMEDIATE")

        subscription = connection.execute(
            """
            SELECT *
            FROM subscriptions

            WHERE verification_token_hash = ?
              AND status = 'pending_verification'
            """,
            (token_hash,)
        ).fetchone()

        if not subscription:

            connection.commit()

            return {
                "success": False,
                "message": "Invalid or already-used verification link."
            }

        expires_at = datetime.fromisoformat(
            subscription["verification_expires_at"]
        )

        if utc_now() > expires_at:

            connection.commit()

            return {
                "success": False,
                "message": "This verification link has expired."
            }

        unsubscribe_token = secrets.token_urlsafe(32)

        unsubscribe_hash = hash_token(
            unsubscribe_token
        )

        connection.execute(
            """
            UPDATE subscriptions

            SET status = 'active',
                verified_at = ?,
                verification_token_hash = NULL,
                verification_expires_at = NULL,
                unsubscribe_token_hash = ?,
                unsubscribed_at = NULL

            WHERE id = ?
            """,
            (
                utc_now().isoformat(),
                unsubscribe_hash,
                subscription["id"]
            )
        )

        connection.commit()

    return {
        "success": True,
        "email": subscription["email"],
        "unsubscribe_token": unsubscribe_token
    }


# --------------------------------------------------
# Unsubscribe
# --------------------------------------------------

def unsubscribe(token):

    initialize_database()

    token_hash = hash_token(token)

    with database_connection() as connection:

        connection.execute("BEGIN IMMEDIATE")

        subscription = connection.execute(
            """
            SELECT id
            FROM subscriptions

            WHERE unsubscribe_token_hash = ?
              AND status = 'active'
            """,
            (token_hash,)
        ).fetchone()

        if not subscription:

            connection.commit()
            return False

        connection.execute(
            """
            UPDATE subscriptions

            SET status = 'unsubscribed',
                unsubscribed_at = ?,
                unsubscribe_token_hash = NULL

            WHERE id = ?
            """,
            (
                utc_now().isoformat(),
                subscription["id"]
            )
        )

        connection.commit()

    return True


# --------------------------------------------------
# Retrieve Subscriptions
# --------------------------------------------------

def get_subscriptions():

    initialize_database()

    with database_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                id,
                email,
                aoi_name,
                species_json,
                time_interval,
                status,
                created_at,
                verified_at,
                unsubscribed_at
                last_checked_at
                
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