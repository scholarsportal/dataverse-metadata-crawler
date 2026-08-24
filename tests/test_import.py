"""Test dataverse-metadata-crawler."""

import dvmeta


def test_import() -> None:
    """Test that the package can be imported."""
    assert isinstance(dvmeta.__name__, str)
