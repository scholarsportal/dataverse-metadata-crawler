"""Timestamp service for the crawling process."""

# ruff: noqa: DTZ005
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Timestamps:
    """A dataclass to store start and end timestamps for the crawling process."""

    start_time: datetime
    end_time: datetime | None = None


def get_display_time(time_obj: datetime | None = None) -> str:
    """Return a string representation of the time in the format: YYYY-MM-DD HH:MM:SS.

    Parameters
    ----------
    time_obj : datetime | None, optional
        By default, None.

    Returns
    -------
    str
    """
    if time_obj is None:
        time_obj = datetime.now()
    return time_obj.strftime("%Y-%m-%d %H:%M:%S")


def get_file_timestamp() -> str:
    """Return a string representation of the current time in the format: YYYYMMDD-HHMMSS.

    Returns
    -------
    str
    """
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def get_current_time() -> datetime:
    """Return the current time as a datetime object.

    Returns
    -------
    datetime
    """
    return datetime.now()


def get_elapsed_time(start_time: datetime, end_time: datetime | None = None) -> str:
    """Return the elapsed time since the start time.

    Returns
    -------
    str
    """
    end = end_time or datetime.now()
    elapsed_time = end - start_time
    return str(elapsed_time)
