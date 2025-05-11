"""This module contains functions used in the dvmeta package."""
from typing import Optional

import httpx
import jmespath
from custom_logging import CustomLogger
from httpxclient import HttpxClient


# Set up logging
logger = CustomLogger.get_logger(__name__)


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
            "data[?type=='dataset'].{datasetId: id, protocol: protocol, authority: authority, identifier: identifier, path: path, pathIds: pathIds}",  # noqa: E501
            read_dict[key],  # noqa: PLR1733
        )
        if result:
            for item in result:
                pid = f"{item['protocol']}:{item['authority']}/{item['identifier']}"
                id = item['datasetId']
                path = '/' + item['path'] if item['path'] else None
                path_ids = item['pathIds']
                dict_to_append = {
                    str(id): {  # pid needs to be converted to string if it's not already
                        'CollectionAlias': config['COLLECTION_ALIAS'],
                        'CollectionID': config['COLLECTION_ID'],
                        'datasetPersistentId': pid,
                        'datasetId': id,
                        'path': path,
                        'pathIds': path_ids,
                    }
                }
                write_dict.update(dict_to_append)
        else:
            empty_dv.append(key)
    return empty_dv, write_dict


def check_connection(config: dict) -> tuple[bool, bool]:
    """Check the connection to the dataverse repository.

    Args:
        config (dict): Configuration dictionary
        auth (bool): Check the connection with authentication

    Returns:
        bool: True if the connection is successful
        bool: True if the connection is successful with authentication
    """
    base_url = config.get('BASE_URL')
    api_key = config.get('API_KEY')
    auth_headers = {'X-Dataverse-key': api_key} if api_key and api_key.lower() != 'none' else {}
    auth_url = f'{base_url}/api/mydata/retrieve?role_ids=8&dvobject_types=Dataverse&published_states=Published&per_page=1'  # noqa: E501
    public_url = f'{base_url}/api/info/version'

    try:
        with HttpxClient(config) as httpx_client:
            if auth_headers:
                logger.print('Checking the connection to the Dataverse repository with authentication...')
                response = httpx_client.sync_get(auth_url)
                if response and response.status_code == httpx_client.httpx_success_status:
                    logger.print(f'Connection to the dataverse repository {config["BASE_URL"]} is successful.')
                    return True, True
                logger.warning('Your API_KEY is invalid. The crawler will now fall back using unauthenticated connection.')

            # Attempt to connect to the repository without authentication
            response = httpx_client.sync_get(public_url)
            if response and response.status_code == httpx_client.httpx_success_status:
                logger.print(f'Unauthenticated connection to the dataverse repository {config["BASE_URL"]} is successful. The script continue crawling.\n')  # noqa: E501
                return True, False
            logger.error(f'Failed to connect to the dataverse repository {config["BASE_URL"]}.\nExiting...')  # noqa: E501
            return False, False

    except httpx.HTTPStatusError as e:
        logger.error(f'Failed to connect to the dataverse repository {config["BASE_URL"]}: HTTP Error {e.response.status_code}')  # noqa: E501
        return False, False

def add_path_to_dataverse_contents(des_dict: dict, ref_dict: dict) -> dict:
    """Add pathIds and path to dataverse_contents from collections_tree_flatten.

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
                    item.update({'pathIds': ref_dict[key]['pathIds']})
            else:
                value['data'].append({'path': ref_dict[key]['path']})
                value['data'].append({'pathIds': ref_dict[key]['pathIds']})
    return des_dict


def add_path_info(meta_dict: dict, ds_dict: dict) -> tuple:
    """Add path_info to the metadata dictionary, handling nested structures."""
    ds_dict_copy = ds_dict.copy()
    for pid_key, pid_value in list(ds_dict_copy.items()):
        pid_key_str = str(pid_key)
        # Traverse the meta_dict to find matching datasetId
        for _meta_key, meta_value in meta_dict.items():
            if isinstance(meta_value, dict) and meta_value.get('data', {}).get('datasetId') == int(pid_key_str):
                # Add path_info to the appropriate nested dictionary
                meta_value['path_info'] = pid_value
                # Remove from ds_dict_copy
                ds_dict_copy.pop(pid_key)
                break

    return meta_dict, ds_dict_copy


def add_permission_info(meta_dict: dict, permission_dict: Optional[dict] = None) -> dict:
    """Add permission_info to the metadata dictionary, handling nested structures."""
    if isinstance(permission_dict, dict):
        for pid_key, pid_value in list(permission_dict.items()):
            pid_key_str = str(pid_key)
            # Traverse the meta_dict to find matching datasetId
            for _meta_key, meta_value in meta_dict.items():
                if isinstance(meta_value, dict) and meta_value.get('data', {}).get('datasetId') == int(pid_key_str):
                    # Add path_info to the appropriate nested dictionary
                    meta_value['permission_info'] = pid_value
                    # Remove from permission_dict
                    permission_dict.pop(pid_key)
                    break
    for _meta_key, meta_value in meta_dict.items():
        if 'permission_info' not in meta_value:
            meta_value['permission_info'] = {'status': 'NA', 'data': []}

    return meta_dict


def replace_key_with_dataset_id(dictionary: dict) -> dict:
    """Replace the top-level key in the dictionary with the value of 'datasetId' in the nested 'data'.

    Args:
        dictionary (dict): The original dictionary.

    Returns:
        dict: A new dictionary with keys replaced by the value of 'datasetId'.
    """
    new_dict = {}
    for old_key, value in dictionary.items():
        # Check if the 'data' key exists and has 'datasetId'
        if isinstance(value, dict) and value.get('data', {}).get('datasetId'):
            new_key = value.get('data', {}).get('datasetId')  # Get the value of 'datasetId'
            new_dict[new_key] = value  # Use it as the new key
        else:
            # Keep the original key if 'id' is missing
            new_dict[old_key] = value
    return new_dict


def rm_dd_from_failed_uris(failed_uris: dict, pid_dict_dd: dict) -> dict:
    """Remove the deaccessioned datasets from the failed_uris dictionary.

    Args:
        failed_uris (dict): Dictionary containing the failed URIs
        pid_dict_dd (dict): Dictionary containing the deaccessioned datasets metadata

    Returns:
        dict: Dictionary containing the failed URIs without the deaccessioned datasets
    """
    # Get the datasetPersistentId from the pid_dict_dd
    dd_pids = [v['datasetPersistentId'] for v in pid_dict_dd.values()]

    # Loop through the dd_pids, and remove the item if it contains the pid in the key of the failed_uris
    keys_to_remove = [k for k in failed_uris if any(pid in k for pid in dd_pids)]
    for k in keys_to_remove:
        failed_uris.pop(k)

    return failed_uris
