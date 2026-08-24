"""utility functions for crawler."""

from typing import Literal

from loguru import logger

from dvmeta.models.publication_status import PublicationStatus


def parse_search_response(
    items: list[dict], publication_status: PublicationStatus | None = None
) -> list:
    """Parse the search response to extract dataset metadata.

    Args:
        items: The items field returned by the Search API response.
        publication_status: The publication status to filter the items by, by default None.

    Returns:
        list: Deduplicated dataset entity IDs.
    """
    if publication_status:
        items = [
            item for item in items if publication_status in item.get("publicationStatuses", [])
        ]

    if not items:
        logger.warning("No items found in the search response.")
        return []

    return list(
        dict.fromkeys([item.get("entity_id") for item in items])
    )  # remove duplicates while preserving order. One dataset might have multiple versions, like DRAFT and PUBLISHED.


def merge_permission_to_meta_dict(meta_dict: dict, permission_metadata: dict) -> dict:
    """Merge permission metadata into the meta_dict.

    Args:
        meta_dict: The original metadata dictionary containing dataset metadata.
        permission_metadata: The permission metadata dictionary to merge in, keyed by dataset ID.

    Returns:
        dict: The merged metadata dictionary with permission metadata included.
    """
    permission_metadata = {
        str(k): v for k, v in permission_metadata.items()
    }  # Convert keys to str for JSON serialization

    meta_dict_copy = meta_dict.copy()  # Avoid mutating the caller's dict

    for dataset_id in meta_dict:
        permissions = permission_metadata.get(str(dataset_id))
        if permissions is not None:
            meta_dict_copy[dataset_id]["permissions"] = permissions
        else:
            logger.debug(f"No permission metadata found for dataset ID {dataset_id}.")

    # Standardize output: ensure every dataset has a permissions key
    for dataset_meta in meta_dict_copy.values():
        dataset_meta.setdefault("permissions", None)

    return meta_dict_copy


def get_total_count_from_response(response: dict) -> int:
    """Extract the total count of items from the search response.

    Args:
        response: The search response dictionary.

    Returns:
        int: The total count of items in the search response.
    """
    return response.get("data", {}).get("total_count", 0)


def get_start_parameters(total_count: int, per_page: int) -> tuple[int, ...]:
    """Calculate the start parameters for pagination.

    Args:
        total_count: The total number of items to paginate.
        per_page: The number of items to display per page.

    Returns:
        tuple[int, ...]: A tuple of start parameters for pagination.

    Raises:
        ValueError: If per_page is not a positive integer.
    """
    if per_page <= 0:
        msg = "per_page must be a positive integer."
        raise ValueError(msg)

    if per_page >= total_count:
        return (0,)

    total_count -= 1  # The start parameter is 0-indexed

    indexes = list(range(0, total_count, per_page))

    return tuple(indexes)
