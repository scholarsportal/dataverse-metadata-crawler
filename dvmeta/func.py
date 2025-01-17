"""This module contains functions used in the dvmeta package."""
import os
import re

import httpx
import jmespath
import typer
from dotenv import load_dotenv
from httpxclient import HttpxClient


def get_pids(read_dict: dict, config: dict) -> tuple:
    """Get URIs in collections_tree_flatten/root_datasets.

    And append them to pid_dict.

    Args:
        read_dict (dict): Dictionary containing the metadata of datasets
        config (dict): Configuration dictionary

    Returns:
        list: List of empty datasets
        dict: Dictionary containing the URIs
    """
    empty_dv = []
    write_dict = {}
    for key, _item in read_dict.items():
        result = jmespath.search(
            "data[?type=='dataset'].{ds_id: id, protocol: protocol, authority: authority, identifier: identifier, path: path, path_ids: path_ids}",  # noqa: E501
            read_dict[key],  # noqa: PLR1733
        )
        if result:
            for item in result:
                pid = f"{item['protocol']}:{item['authority']}/{item['identifier']}"
                ds_id = item['ds_id']
                path = '/' + item['path'] if item['path'] else None
                path_ids = item['path_ids']
                dict_to_append = {
                    str(pid): {  # pid needs to be converted to string if it's not already
                        'collection_alias': config['COLLECTION_ALIAS'],
                        'collection_id': config['COLLECTION_ID'],
                        'pid': pid,
                        'ds_id': ds_id,
                        'path': path,
                        'path_ids': path_ids,
                    }
                }
                write_dict.update(dict_to_append)
        else:
            empty_dv.append(key)
    return empty_dv, write_dict


def check_connection(config: dict) -> bool:
    """Check the connection to the dataverse repository.

    Args:
        config (dict): Configuration dictionary
        auth (bool): Check the connection with authentication

    Returns:
        bool: True if the connection is successful, False otherwise
    """
    if config.get('API_KEY'):
        url = f"{config['BASE_URL']}/api/mydata/retrieve?role_ids=8&dvobject_types=Dataverse&published_states=Published&per_page=1"  # noqa: E501
        config['HEADERS'] = {'X-Dataverse-key': config['API_KEY']}
        print('Checking the connection to the dataverse repository with authentication...\n')  # noqa: E501
    else:
        url = f"{config['BASE_URL']}/api/info/version"
        config['HEADERS'] = {}
        print('Checking the connection to the dataverse repository without authentication...\n')  # noqa: E501
    try:
        with HttpxClient(config) as httpx_client:
            response = httpx_client.sync_get(url)
            if response and response.status_code == httpx_client.httpx_success_status:
                print(f'Connection to the dataverse repository {config["BASE_URL"]} is successful.\n')  # noqa: E501
                return True
            print('Your API_KEY is invalid and therefore failed to connect to the dataverse repository. Please check your input.\n')  # noqa: E501
            return False
    except httpx.HTTPStatusError as e:
        print(f'Failed to connect to the dataverse repository {config["BASE_URL"]}: HTTP Error {e.response.status_code}\n')  # noqa: E501
        return False


def version_type(value: str) -> str:
    """Validate the value of --version argument.

    Args:
        value (str): Value of --version argument.

    Returns:
        str: Value of --version argument if it is valid.

    Raises:
        typer.BadParameter: If the value is not valid.
    """
    valid_special_versions = {'draft', 'latest', 'latest-published'}

    # Normalize and validate the input
    value = str(value).lower().strip()

    if value in valid_special_versions or re.match(r'^\d+(\.\d+)?$', value):
        return value
    msg = f'Invalid value for --version: "{value}".\nMust be "draft", "latest", "latest-published", or a version number like "x" or "x.y".'  # noqa: E501
    raise typer.BadParameter(
        msg
    )


def validate_spreadsheet(value: bool, dvdfds_metadata: bool) -> bool:
    """Validate the value of --spreadsheet argument."""
    if value and not dvdfds_metadata:
        msg = 'The --spreadsheet option can only be used if --dvdfds_metadata is set to True.'
        raise typer.BadParameter(msg)
    return value


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


def add_path_to_dataverse_contents(des_dict: dict, ref_dict: dict) -> dict:
    """Add path_ids and path to dataverse_contents from collections_tree_flatten.

    Args:
        des_dict (dict): Dictionary containing the metadata of datasets
        ref_dict (dict): Dictionary containing the metadata of dataverses

    Returns:
        dict: Dictionary containing the metadata of datasets with path_ids and path added
    """  # noqa: W505
    for key, value in des_dict.items():
        if key in ref_dict:
            if value['data']:
                for item in value['data']:
                    item.update({'path': ref_dict[key]['path']})
                    item.update({'path_ids': ref_dict[key]['path_ids']})
            else:
                value['data'].append({'path': ref_dict[key]['path']})
                value['data'].append({'path_ids': ref_dict[key]['path_ids']})
    return des_dict


def add_path_info(meta_dict: dict, pid_dict: dict) -> tuple:
    """Add path_info to the metadata dictionary."""
    pid_dict_copy = pid_dict.copy()
    for key in list(pid_dict_copy.keys()):
        if key in meta_dict:
            meta_dict[key]['path_info'] = pid_dict_copy[key]
            pid_dict_copy.pop(key)

    return meta_dict, pid_dict_copy


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
