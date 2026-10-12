
# --------------------------------------------------
# Imports
# --------------------------------------------------

from datetime import datetime, timezone, timedelta

from src.backend.subscription_service import get_subscriptions
from src.backend.time_intervals import TIME_INTERVALS


# --------------------------------------------------
# Current UTC Time
# --------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc)


# --------------------------------------------------
# Determine When a Subscription Is Due
# --------------------------------------------------

def is_subscription_due(subscription, now):

    interval_key = subscription["time_interval"]

    interval_hours = TIME_INTERVALS[interval_key]["hours"]

    last_checked = subscription["last_checked_at"]

    if last_checked:
        starting_time = datetime.fromisoformat(last_checked)
    else:
        starting_time = datetime.fromisoformat(
            subscription["verified_at"]
        )

    next_check = starting_time + timedelta(
        hours=interval_hours
    )

    due = now >= next_check

    return due, next_check


# --------------------------------------------------
# Retrieve Active Subscriptions
# --------------------------------------------------

def get_active_subscriptions():

    subscriptions = get_subscriptions()

    active_subscriptions = []

    for subscription in subscriptions:

        if subscription["status"] == "active":
            active_subscriptions.append(subscription)

    return active_subscriptions


# --------------------------------------------------
# Scheduler Dry Run
# --------------------------------------------------

def run_scheduler_dry_run():

    print("\nATTUNE2NATURE - SCHEDULER DRY RUN")
    print("=" * 60)

    now = utc_now()

    print("Current UTC Time:", now.isoformat())

    active_subscriptions = get_active_subscriptions()

    print("\nActive Subscriptions:", len(active_subscriptions))

    if not active_subscriptions:
        print("No active subscriptions to process.")
        return

    for subscription in active_subscriptions:

        due, next_check = is_subscription_due(
            subscription,
            now
        )

        print("\n" + "-" * 60)

        print("Subscription ID:", subscription["id"])
        print("AOI:", subscription["aoi_name"])
        print("Species:", ", ".join(subscription["species"]))
        print("Frequency:", subscription["time_interval"])
        print("Next Check:", next_check.isoformat())
        print("Due Now:", due)

        if due:
            print("Action: Ready for observation query")
        else:
            print("Action: Waiting for next scheduled check")

    print("\nDRY RUN COMPLETE")
    print("No observations queried.")
    print("No emails sent.")


# --------------------------------------------------
# Run Locally
# --------------------------------------------------

if __name__ == "__main__":
    run_scheduler_dry_run()
