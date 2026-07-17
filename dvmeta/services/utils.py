"""This module contains utility functions for the dvmeta package."""

import math
from hashlib import sha256
from pathlib import Path

import jmespath


def count_key(key: dict | list | tuple) -> int:
    """Count the number of keys in a dictionary, list or tuple.

    Args:
        key (dict, list, tuple): The dictionary, list or tuple to count the keys of.

    Returns:
        int: The number of keys in the dictionary, list or tuple.
    """
    return len(key) if isinstance(key, (dict, list, tuple)) else 0


def convert_size(size_bytes: int | str) -> str:
    """Convert the size of a file from bytes to a human-readable format.

    Args:
        size_bytes (int): The size of the file in bytes.

    Returns:
        str: The size of the file in a human-readable format
    """
    if not isinstance(size_bytes, int):
        return 'Error'
    if size_bytes == 0:
        return '0B'
    size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f'{s} {size_name[i]}'


def gen_checksum(file_path: Path) -> str:
    """Generate a SHA-256 checksum for a file.

    Args:
        file_path (Path): The path to the file for which to generate the checksum.

    Returns:
        str: The SHA-256 checksum of the file.
    """
    sha256_hash = sha256()
    with file_path.open('rb') as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()  # Return the hexadecimal digest of the hash


def get_data_files_size(dictionary: dict) -> int | str:
    """Calculate the total size of data files in bytes from a dataset metadata dictionary.

    Args:
        dictionary (dict): A dictionary containing dataset metadata, expected to have a structure where the latest version's files can be accessed via 'datasetVersion.files'.

    Returns:
        int: The total size of data files in bytes if the structure is correct and files are present.

        str: 'Error' if the input is not a dictionary or if the expected structure is not found.
    """  # noqa: E501, W505
    ds_version = dictionary.get('datasetVersion', {})
    if ds_version.get('files'):
        data_files_size_list: list = jmespath.search('datasetVersion.files[*].dataFile.filesize|[]', dictionary)
        if data_files_size_list:
            return sum(data_files_size_list)
    else:
        return 0
    return 'Error'


def get_collection_files_size(dictionary: dict) -> int | str:
    """Calculate the total size of collection files in bytes from a dataset metadata dictionary.

    Args:
        dictionary (dict): A dictionary containing dataset metadata, expected to have a structure where the latest version's files can be accessed via '{dataset_id}.data.datasetVersion.files'.
    """  # noqa: E501, W505
    total_size = 0

    for _, dataset in dictionary.items():
        ds_size = get_data_files_size(dataset)
        total_size += ds_size if isinstance(ds_size, int) else 0
    return total_size


def get_data_files_count(dictionary: dict) -> int | str:
    """Calculate the total number of data files from a dataset metadata dictionary.

    Args:
        dictionary (dict): A dictionary containing dataset metadata, expected to have a structure where the latest version's files can be accessed via 'datasetVersion.files'.

    Returns:
        int | str: The total number of data files if the structure is correct and files are present, otherwise 'Error'.
    """  # noqa: E501, W505
    ds_version = dictionary.get('datasetVersion', {})
    if 'files' in ds_version:
        return len(ds_version['files'])
    return 'Error'


def get_collection_files_count(dictionary: dict) -> int | str:
    """Calculate the total number of data files from a dataset metadata dictionary of a collection.

    Args:
        dictionary (dict): A dictionary containing dataset metadata, expected to have a structure where the latest version's files can be accessed via '{dataset_id}.data.datasetVersion.files'.
    """  # noqa: E501, W505
    total_count = 0

    for _, dataset in dictionary.items():
        ds_count = get_data_files_count(dataset)
        total_count += ds_count if isinstance(ds_count, int) else 0
    return total_count
