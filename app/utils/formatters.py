"""Formatting helpers for the PetCare app (e.g., datetimes for templates)."""

from datetime import timezone
from zoneinfo import ZoneInfo


def localdt(dt, tz_name: str = "Europe/Madrid", fmt: str = "%Y-%m-%d %H:%M"):
    """Render a datetime in the given IANA timezone.

    If `dt` is naive, treat it as UTC. Returns '' for None.
    """
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Europe/Madrid")
    return dt.astimezone(tz).strftime(fmt)