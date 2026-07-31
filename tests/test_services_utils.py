"""Test services/utils.py."""

import pytest

from dvmeta.services.utils import count_key


@pytest.mark.parametrize(
    ("data", "expected_count"),
    [
        (["a"], 1),
        (["a", "b", "c"], 3),
        ([], 0),
        ({}, 0),
        ((), 0),
        ((None, None), 2),
        ({"key1": "value1", "key2": "value2"}, 2),
        (("x", "y", "z"), 3),
        ("x", 0),
    ],
)
def test_count_key(data, expected_count):
    """Test count_key function."""
    assert count_key(data) == expected_count
