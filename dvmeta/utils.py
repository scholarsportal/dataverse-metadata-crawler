"""This module contains utility functions for the dvmeta package."""
import math
import os
from hashlib import sha256
from pathlib import Path
from typing import Any

import jmespath
import orjson
from custom_logging import CustomLogger
from dirmanager import DirManager
from dotenv import load_dotenv
from models import CollectionData
from timestamp import Timestamp


# Initialize the logger
logger = CustomLogger().get_logger(__name__)


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


def list_to_string(list: list) -> str:
    """Joins list items into comma-separated string after converting to string and stripping whitespace.

    Args:
        list (list): A list of values to be processed.

    Returns:
        str: A single string with the processed values separated by commas.
    """
    # Ensure each value is a string and strip whitespace from each string
    stripped_values = [str(value).strip() for value in list]

    # Join the stripped strings with a comma
    return ', '.join(stripped_values)


def orjson_export(data_dict: dict, file_name: str) -> tuple:
    """Export a dictionary to a json file using the orjson library.

    Args:
        data_dict (dict): The dictionary to export to a json file.
        file_name (str): The name of the json file to create.

    Returns:
        tuple(Path, str): A tuple containing the path to the created json file and its checksum.
    """
    json_dir = DirManager().json_files_dir()
    json_file_path = Path(json_dir, f'{file_name}_{Timestamp().get_file_timestamp()}.json')
    if data_dict:
        with json_file_path.open('wb') as file:  # Open file in binary write mode
            file.write(orjson.dumps(data_dict, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS))
        checksum = gen_checksum(json_file_path)
        logger.print(f'Exported {file_name} to json file: {json_file_path}'
              f'\nChecksum (SHA-256): {checksum}')

        return json_file_path, checksum
    logger.print(f'{file_name} is empty, no json file is created.')

    return None, None


def flatten_collection(readdict, path_name='', path_ids=[]) -> dict:
    """Flatten a nested collection in a dictionary.

    Args:
        readdict (dict): The dictionary to flatten.
        path_name (str): The path name.
        path_ids (list): The path IDs.

    Returns:
        dict: The flattened dictionary.
    """
    write_dict = {}
    dictionary_data = readdict['data']

    def loop_item(dictionary_data, path_name='', path_ids=[]):
        """Loop through the items in the dictionary and flatten them.

        Args:
            dictionary_data (dict): The dictionary to loop through.
            path_name (str): The path name.
            path_ids (list): The path IDs.

        Returns:
            dict: The flattened dictionary.
        """
        for item in dictionary_data['children']:
            new_item = item.copy()

            current_path_ids = path_ids + [item['id']]

            new_item['pathIds'] = current_path_ids
            new_item['path'] = f"{path_name}/{item['name']}" if path_name else item['name']
            new_item.pop('children', None)
            write_dict[item['id']] = new_item
            if 'children' in item:
                loop_item(item, new_item['path'], current_path_ids)
        return write_dict
    if 'children' not in dictionary_data or not dictionary_data['children']:
        return {}
    return loop_item(dictionary_data, path_name, path_ids)


def load_env() -> dict:
    """Load the environment variables.

    Returns:
        dict: A dictionary containing the environment variables
    """
    # Load the environment variables
    load_dotenv()

    config = {
        'API_KEY': os.getenv('API_KEY', None),
        'BASE_URL': os.getenv('BASE_URL'),
        'TIMEOUT': None,
    }
    if config['API_KEY']:
        config['HEADERS'] = {'X-Dataverse-key': config['API_KEY'], 'Accept': 'application/json'}
    else:
        config['HEADERS'] = {'Accept': 'application/json'}
    return config


def count_files_size(read_dict: dict) -> tuple:
    """Count the number of files and the total size of files in the dataset.

    Args:
        read_dict (dict): Dictionary containing the metadata of datasets

    Returns:
        int: Total number of files in the dataset
        int: Total size of files in the dataset
    """
    filecount_list = []
    filesize_list = []
    for key, _item in read_dict.items():
        if read_dict.get(key).get('data').get('files'):  # type: ignore
            filecount_list.append(len(read_dict.get(key).get('data').get('files')))  # type: ignore
            filesize_list.append(sum(jmespath.search('data.files[*].dataFile.filesize|[]', read_dict[key])))  # noqa: PLR1733
        else:
            filecount_list.append(0)
            filesize_list.append(0)

    return sum(filecount_list), sum(filesize_list)


def update_config_with_collection_data(config: dict[str, Any], collection_data: CollectionData) -> dict[str, Any]:
    """Update the config dictionary with collection data.

    Args:
        config (dict): The config dictionary to update
        collection_data (CollectionData): The validated collection data

    Returns:
        dict: The updated config
    """
    config['COLLECTION_ID'] = collection_data.id
    config['COLLECTION_ALIAS'] = collection_data.alias
    config['COLLECTION_NAME'] = collection_data.name
    return config
