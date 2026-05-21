"""Dynamic posted-time formatting for jobs within the last 24 hours."""
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
SECONDS_24H = 86400


def seconds_since_posted(updated_ts):
    if not updated_ts:
        return None
    try:
        ts = int(updated_ts)
    except (TypeError, ValueError):
        return None
    return max(0, int(time.time()) - ts)


def is_within_24h(updated_ts):
    diff = seconds_since_posted(updated_ts)
    if diff is None:
        return False
    return diff <= SECONDS_24H


def format_posted_time(updated_ts):
    """
    Relative + exact clock time from Simplify updated_date/start_date.
    Examples: "37 min ago · Today 5:57 AM", "Yesterday 4:30 PM", "2 hours ago · Today 3:15 PM"
    Returns None if older than 24h.
    """
    diff = seconds_since_posted(updated_ts)
    if diff is None:
        return "Recently"
    if diff > SECONDS_24H:
        return None

    ts = int(updated_ts)
    post_dt = datetime.fromtimestamp(ts, tz=TZ)
    now_dt = datetime.fromtimestamp(int(time.time()), tz=TZ)
    time_str = post_dt.strftime("%I:%M %p").lstrip("0")

    if diff < 60:
        return f"Just now · Today {time_str}"

    post_date = post_dt.date()
    today = now_dt.date()
    yesterday = today - timedelta(days=1)

    if diff < 3600:
        m = diff // 60
        rel = f"{m} min ago"
        if post_date == today:
            return f"{rel} · Today {time_str}"
        if post_date == yesterday:
            return f"{rel} · Yesterday {time_str}"
        return f"{rel} · {time_str}"

    h = diff // 3600
    rel = f"{h} hour{'s' if h != 1 else ''} ago"

    if post_date == today:
        return f"{rel} · Today {time_str}"
    if post_date == yesterday:
        return f"Yesterday · {time_str}"
    return f"{rel} · {post_dt.strftime('%b %d')} {time_str}"
