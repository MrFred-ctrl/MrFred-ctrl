"""SpaceX API data fetching."""

import requests
from datetime import datetime, timezone


BASE_URL = "https://api.spacexdata.com/v4/launches"
TIMEOUT = 10


def get_upcoming_launch():
    """Fetch the next upcoming SpaceX launch."""
    try:
        resp = requests.get(f"{BASE_URL}/upcoming", timeout=TIMEOUT)
        resp.raise_for_status()
        launches = resp.json()
        # Sort by date_unix ascending, take first
        launches_sorted = sorted(
            [l for l in launches if l.get("date_unix")],
            key=lambda x: x["date_unix"],
        )
        if not launches_sorted:
            return None
        return launches_sorted[0]
    except Exception:
        return None


def get_latest_launch():
    """Fetch the most recent past SpaceX launch."""
    try:
        resp = requests.get(f"{BASE_URL}/latest", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def format_countdown(date_unix):
    """Return a human-readable countdown string from a unix timestamp."""
    if not date_unix:
        return "Unknown"
    now = datetime.now(timezone.utc).timestamp()
    delta = int(date_unix - now)
    if delta < 0:
        return "Launched"
    days = delta // 86400
    hours = (delta % 86400) // 3600
    minutes = (delta % 3600) // 60
    return f"{days}d {hours}h {minutes}m"


def format_date(date_utc):
    """Format an ISO date string into a readable format."""
    if not date_utc:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(date_utc.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return date_utc


def get_launch_info(launch):
    """Extract display fields from a launch dict."""
    if not launch:
        return {}
    return {
        "name": launch.get("name", "Unknown"),
        "date_utc": format_date(launch.get("date_utc")),
        "date_unix": launch.get("date_unix"),
        "rocket_id": launch.get("rocket", "Unknown"),
        "success": launch.get("success"),
        "details": launch.get("details") or "No details available.",
        "countdown": format_countdown(launch.get("date_unix")),
    }
