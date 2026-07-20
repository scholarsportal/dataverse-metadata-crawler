"""utility functions for crawler."""

from typing import Literal

from loguru import logger


def parse_search_response(
    items: list[dict],
    publication_status: Literal["Draft", "Published", "Unpublished"] | None = None,
) -> list:
    """Parse the search response to extract dataset metadata.

    Parameters
    ----------
    publication_status : Literal["Draft", "Published", "Unpublished"] | None, optional
        The publication status to filter the items by, by default None
    items : list[dict]
        The items field returned by the Search API response.

    Returns
    -------
    list
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


def extract_path(node: dict, dataset_name: str) -> str:
    """Walk schema:isPartOf chain from leaf to root, return ordered path.

    Parameters
    ----------
    node : dict
        The current node in the schema:isPartOf chain.

    dataset_name : str
        The name of the dataset.

    Returns
    -------
    str: The ordered path from the root to the dataset.

    """
    path = []
    current = node
    while current:
        path.append({"name": current.get("schema:name"), "id": current.get("@id")})
        current = current.get("schema:isPartOf")

    collections_path = "/".join(p["name"] for p in reversed(path))

    return collections_path + "/" + dataset_name


def get_path_from_oaiore(oaiore_response: dict) -> str | None:
    """Extract the dataset path from the OAI_ORE metadata.

    Parameters
    ----------
    oaiore_response : dict
        The OAI_ORE metadata response.

    Returns
    -------
    str | None
        The dataset path if found, otherwise None.
    """
    dataset_name = oaiore_response.get("ore:describes", {}).get("schema:name")
    ispartof = oaiore_response.get("ore:describes", {}).get("schema:isPartOf", [])
    if not ispartof:
        return None

    return extract_path(ispartof, dataset_name)


def merge_permission_to_meta_dict(meta_dict: dict, permission_metadata: dict) -> dict:
    """Merge permission metadata into the meta_dict.

    Parameters
    ----------
    permission_metadata : dict
        The permission metadata dictionary to merge, which contains dataset permissions.
    meta_dict : dict
        The original metadata dictionary containing dataset metadata.

    Returns
    -------
    dict: The merged metadata dictionary with permission metadata included.
    """
    permission_metadata = {
        str(k): v for k, v in permission_metadata.items()
    }  # Convert keys to str for JSON serialization

    meta_dict_copy = meta_dict.copy()  # Create a copy to avoid modifying the original dictionary

    for dataset_id in meta_dict:
        permissions = permission_metadata.get(str(dataset_id))
        if permissions is not None:
            meta_dict_copy[dataset_id]["permissions"] = permissions
        else:
            logger.debug(f"No permission metadata found for dataset ID {dataset_id}.")

    # Add dataset_meta['permissions'] = None to standardize the output for datasets without permissions
    for dataset_meta in meta_dict_copy.values():
        dataset_meta.setdefault("permissions", None)

    return meta_dict_copy


def get_total_count_from_response(response: dict) -> int:
    """Extract the total count of items from the search response.

    Parameters
    ----------
    response : dict
        The search response dictionary.

    Returns
    -------
    int: The total count of items in the search response.
    """
    return response.get("data", {}).get("total_count", 0)


def get_start_parameters(total_count: int, per_page: int) -> tuple[int, ...]:
    """Calculate the start parameters for pagination.

    Parameters
    ----------
    per_page : int
        The number of items to display per page.
    total_count : int
        The total number of items to paginate.

    Returns
    -------
    tuple[int, ...]
        A tuple of start parameters for pagination.

    Raises
    ------
    ValueError
        If per_page is not a positive integer.
    """
    if per_page <= 0:
        msg = "per_page must be a positive integer."
        raise ValueError(msg)

    if per_page >= total_count:
        return (0,)

    total_count -= 1  # The start parameter is 0-indexed

    indexes = list(range(0, total_count, per_page))

    return tuple(indexes)
