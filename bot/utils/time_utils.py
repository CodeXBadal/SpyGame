"""Time helpers."""
from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


def to_epoch(dt: datetime) -> int:
    """Convert a datetime to unix seconds, assuming UTC if naive."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def human_duration(seconds: int) -> str:
    """Render seconds as a short human string like '2m 5s'."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {sec}s" if sec else f"{minutes}m"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"
