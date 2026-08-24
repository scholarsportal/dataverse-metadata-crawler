"""Test services/utils.py."""

from hashlib import sha256
from pathlib import Path

import pytest

from dvmeta.services.utils import convert_size, count_key, gen_checksum


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


@pytest.mark.parametrize(
    ("size_bytes", "expected_size"),
    [
        (0, "0 B"),
        (1024, "1.0 KB"),
        (4565, "4.46 KB"),
        (1048576, "1.0 MB"),
        (1073741824, "1.0 GB"),
        (1099511627776, "1.0 TB"),
        (1099511627876, "1.0 TB"),
        (1125899906842624, "1.0 PB"),
        (str(0), "0 B"),
        (str(1024), "1.0 KB"),
        (str([]), "Error"),
        ("x", "Error"),
        (None, "Error"),
        ([], "Error"),
    ],
)
def test_convert_size(size_bytes, expected_size):
    """Test convert_size function."""
    assert convert_size(size_bytes) == expected_size


@pytest.mark.parametrize(
    "file_content",
    [
        b"Hello, World!",
        b"",
        b"\x00\x01\x02" * 5000,  # spans multiple 4096-byte read blocks
    ],
)
def test_gen_checksum(file_content: bytes, tmp_path: Path) -> None:
    """gen_checksum matches hashlib.sha256 computed directly on the same bytes."""
    file_path = tmp_path / "file.bin"
    file_path.write_bytes(file_content)

    assert gen_checksum(file_path) == sha256(file_content).hexdigest()
