from datetime import datetime, timezone


def create_timestamp() -> datetime:
    """Get the current UTC timestamp."""
    return datetime.now(timezone.utc)
