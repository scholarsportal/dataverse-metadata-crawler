"""Utility functions for the dvmeta package."""

import math
from hashlib import sha256
from pathlib import Path
from typing import Any

import jmespath


def count_key(key: dict | list | tuple | Any) -> int:  # ruff:ignore[any-type]
    """Count the number of keys in a dictionary, list or tuple.

    Args:
        key: The collection to count.

    Returns:
        int: The number of keys, or 0 if `key` isn't a dict, list, or tuple.
    """
    return len(key) if isinstance(key, (dict, list, tuple)) else 0


def convert_size(size_bytes: int | str) -> str:
    """Convert the size of a file from bytes to a human-readable format.

    Args:
        size_bytes: The size in bytes.

    Returns:
        str: The human-readable size (e.g. "1.5 MB"), or "Error" if `size_bytes` isn't an int.
    """
    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return "Error"
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = math.floor(math.log(size_bytes, 1024))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def gen_checksum(file_path: Path) -> str:
    """Generate a SHA-256 checksum for a file.

    Args:
        file_path: The file to checksum.

    Returns:
        str: The hexadecimal SHA-256 digest.
    """
    sha256_hash = sha256()
    with file_path.open("rb") as f:
        # Read in 4K blocks to avoid loading the whole file into memory
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_data_files_size(dictionary: dict) -> int | str:
    """Calculate the total size of data files in bytes from a dataset metadata dictionary.

    Args:
        dictionary: Dataset metadata, with files accessible via 'datasetVersion.files'.

    Returns:
        int | str: The total size in bytes, 0 if there are no files, or "Error" on failure.
    """
    ds_version = dictionary.get("datasetVersion", {})
    if ds_version.get("files"):
        data_files_size_list: list = jmespath.search(
            "datasetVersion.files[*].dataFile.filesize|[]", dictionary
        )
        if data_files_size_list:
            return sum(data_files_size_list)
    else:
        return 0
    return "Error"


def get_collection_files_size(dictionary: dict) -> int | str:
    """Calculate the total size of collection files in bytes from a dataset metadata dictionary.

    Args:
        dictionary: Metadata for a collection of datasets, keyed by dataset ID.

    Returns:
        int | str: The total size in bytes across all datasets.
    """
    total_size = 0

    for dataset in dictionary.values():
        ds_size = get_data_files_size(dataset)
        total_size += ds_size if isinstance(ds_size, int) else 0
    return total_size


def get_data_files_count(dictionary: dict) -> int | str:
    """Calculate the total number of data files from a dataset metadata dictionary.

    Args:
        dictionary: Dataset metadata, with files accessible via 'datasetVersion.files'.

    Returns:
        int | str: The number of files, or "Error" if it can't be computed.
    """
    ds_version = dictionary.get("datasetVersion", {})
    if "files" in ds_version:
        return len(ds_version["files"])
    return "Error"


def get_collection_files_count(dictionary: dict) -> int | str:
    """Calculate the total number of data files from a dataset metadata dictionary of a collection.

    Args:
        dictionary: Metadata for a collection of datasets, keyed by dataset ID.

    Returns:
        int | str: The total number of files across all datasets.
    """
    total_count = 0

    for dataset in dictionary.values():
        ds_count = get_data_files_count(dataset)
        total_count += ds_count if isinstance(ds_count, int) else 0
    return total_count
