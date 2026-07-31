"""Test crawler/utils.py."""

import pytest

from dvmeta.crawler.utils import parse_search_response

FIXTURE_ITEMS = [
    {"entity_id": "1", "publicationStatuses": ["Draft"]},
    {"entity_id": "2", "publicationStatuses": ["Published"]},
    {"entity_id": "3", "publicationStatuses": ["Draft", "Published"]},
    {"entity_id": "4", "publicationStatuses": []},
    {"entity_id": "5", "publicationStatuses": ["Unpublished"]},
]


@pytest.mark.parametrize(
    ("items", "publication_status", "expected"),
    [
        (FIXTURE_ITEMS, "Draft", ["1", "3"]),
        (FIXTURE_ITEMS, "Published", ["2", "3"]),
        (FIXTURE_ITEMS, "Unpublished", ["5"]),
        (FIXTURE_ITEMS, None, ["1", "2", "3", "4", "5"]),
        ([], "Draft", []),
        ([], None, []),
    ],
)
def test_accept_parse_search_response(items, publication_status, expected):
    """Test parse_search_response function."""
    # Test filtering by publication status
    assert parse_search_response(items, publication_status) == expected
