"""Tests services/timestamp.py."""

from datetime import datetime

import pytest

from dvmeta.services.timestamp import (
    get_current_time,
    get_display_time,
    get_elapsed_time,
    get_file_timestamp,
)


@pytest.mark.parametrize(
    ("timestamp", "expected_display_time"),
    [
        (datetime(2024, 1, 1, 12, 0, 0), "2024-01-01 12:00:00"),
        (None, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    ],
)
def test_get_display_time(timestamp, expected_display_time):
    """Test get_display_time function."""
    if timestamp is None:
        # If timestamp is None, we can't assert a specific value, but we can check the format
        assert get_display_time(timestamp).count("-") == 2  # Check for YYYY-MM-DD format
        assert get_display_time(timestamp).count(":") == 2  # Check for HH:MM:SS format
        assert isinstance(get_display_time(timestamp), str)
    else:
        assert get_display_time(timestamp) == expected_display_time


def test_get_file_timestamp():
    """Test get_file_timestamp function."""
    file_timestamp = get_file_timestamp()
    assert len(file_timestamp) == 15  # Format: YYYYMMDD-HHMMSS
    assert file_timestamp[8] == "-"  # Check for the hyphen separator


def test_get_current_time():
    """Test get_current_time function."""
    current_time = get_current_time()
    assert isinstance(current_time, datetime)


@pytest.mark.parametrize(
    ("start_time", "end_time", "expected_elapsed_time"),
    [
        (datetime(2024, 1, 1, 12, 0, 0), datetime(2024, 1, 1, 12, 0, 5), "0:00:05"),
        (
            datetime(2024, 1, 1, 12, 0, 0),
            None,
            "0:00:00",
        ),  # This will depend on the current time, so we can't assert a specific value
    ],
)
def test_get_elapsed_time(start_time, end_time, expected_elapsed_time):
    """Test get_elapsed_time function."""
    elapsed_time = get_elapsed_time(start_time, end_time)
    if end_time is None:
        # If end_time is None, we can't assert a specific value, but we can check the format
        assert isinstance(elapsed_time, str)
    else:
        assert elapsed_time == expected_elapsed_time
        assert isinstance(elapsed_time, str)
