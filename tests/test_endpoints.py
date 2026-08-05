"""Test the endpoints of the dvmeta app."""

import pytest

from dvmeta.services.client.endpoints import Endpoints


@pytest.mark.parametrize(
    "dataset_id, version, return_owners, expected_url",
    [
        ("12345", "latest", True, "api/datasets/12345?returnOwners=true"),
        ("12345", "draft", True, "api/datasets/12345/versions/:draft?returnOwners=true"),
        (
            "12345",
            "latest-published",
            True,
            "api/datasets/12345/versions/:latest-published?returnOwners=true",
        ),
        ("12345", 2, True, "api/datasets/12345/versions/2?returnOwners=true"),
        ("12345", 2.5, True, "api/datasets/12345/versions/2.5?returnOwners=true"),
        ("12345", "invalid_version", False, "api/datasets/12345"),
        ("12345", "invalid_version", True, "api/datasets/12345?returnOwners=true"),
    ],
)
def test_ds_json_endpoint(dataset_id, version, return_owners, expected_url):
    """Test the ds_json endpoint URL generation."""
    url = Endpoints.ds_json(dataset_id, version, return_owners=return_owners)
    assert url == expected_url
