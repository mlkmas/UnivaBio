# src/config.py
"""
Configuration settings for RememberMe AI
"""
from datetime import datetime, timezone, timedelta

# Israel timezone
# WARNING: This is hardcoded and MUST be updated manually for daylight saving.
# UTC+2: Israel Winter Time (Standard Time)
# UTC+3: Israel Summer Time (Daylight Saving)
ISRAEL_TZ = timezone(timedelta(hours=0))

def get_israel_time():
    """Get current time in Israel timezone"""
    # NOTE: This uses the hardcoded ISRAEL_TZ offset.
    # For a robust solution, a library like 'pytz' or 'zoneinfo'
    # with 'Asia/Jerusalem' is recommended.
    return datetime.now(ISRAEL_TZ)

def format_israel_time(dt):
    """Format datetime for Israel timezone"""
    if dt.tzinfo is None:
        # Assume UTC if no timezone
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ISRAEL_TZ)