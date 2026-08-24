"""Timestamp service for the crawling process."""

# ruff:file-ignore[call-datetime-now-without-tzinfo]
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Timestamps:
    """A dataclass to store start and end timestamps for the crawling process."""

    start_time: datetime
    end_time: datetime | None = None


def get_display_time(time_obj: datetime | None = None) -> str:
    """Return a string representation of the time in the format: YYYY-MM-DD HH:MM:SS.

    Args:
        time_obj: The time to format, by default the current time.

    Returns:
        str: The formatted time string.
    """
    if time_obj is None:
        time_obj = datetime.now()
    return time_obj.strftime("%Y-%m-%d %H:%M:%S")


def get_file_timestamp() -> str:
    """Return the current time formatted for use in filenames (YYYYMMDD-HHMMSS)."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def get_current_time() -> datetime:
    """Return the current time."""
    return datetime.now()


def get_elapsed_time(start_time: datetime, end_time: datetime | None = None) -> str:
    """Return the elapsed time since the start time.

    Args:
        start_time: The start time.
        end_time: The end time, by default the current time.

    Returns:
        str: The elapsed time.
    """
    end = end_time or datetime.now()
    elapsed_time = end - start_time
    return str(elapsed_time)
