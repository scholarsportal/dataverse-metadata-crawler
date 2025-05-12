"""Parsing module for parsing data from input files."""

import jmespath
from custom_logging import CustomLogger
from typing import Optional


# Set up logging
logger = CustomLogger.get_logger(__name__)

class Parsing:
    """This class is used to parse the data from the input file."""

    def __init__(self, config: dict, collections_tree: dict):
        self.config = config
        self.collection_tree = collections_tree
        self.collections_tree_flatten = self._flatten_collection(self.collection_tree)
        self.collection_id_list = self.make_collection_list()
        self.dataverse_contents = {}
        self.ds_dict = {'datasetPersistentId': []}
        self.meta_dict = None

    @staticmethod
    def _flatten_collection(readdict: dict, path_name='', path_ids=[]) -> dict:
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

    def add_path_to_dataverse_contents(self, dataverse_contents: dict) -> dict:
        """Add pathIds and path to dataverse_contents from collections_tree_flatten.

        Args:
            dataverse_contents (dict): Dictionary containing the metadata of datasets

        Returns:
            dict: Dictionary containing the metadata of datasets with path_ids and path added
        """  # noqa: W505
        for key, value in dataverse_contents.items():
            if key in self.collections_tree_flatten:
                if value['data']:
                    for item in value['data']:
                        item.update({'path': self.collections_tree_flatten[key]['path']})
                        item.update({'pathIds': self.collections_tree_flatten[key]['pathIds']})
                else:
                    value['data'].append({'path': self.collections_tree_flatten[key]['path']})
                    value['data'].append({'pathIds': self.collections_tree_flatten[key]['pathIds']})
        # Update the dataverse_contents with the new path and pathIds
        self.dataverse_contents = dataverse_contents
        return dataverse_contents

    def make_collection_list(self) -> list:
        """This function creates a list of collection IDs from the collections_tree_flatten."""
        collection_id_list = []

        # Add collection id to collection_id_list
        collection_id_list = [item['id'] for item in self.collections_tree_flatten.values()]

        # Add root collection id to collection_id_list
        collection_id_list.append(self.config['COLLECTION_ID'])

        return collection_id_list

    def get_pids(self) -> tuple:
        """Get URIs in collections_tree_flatten/root_datasets, and append them to pid_dict.

        Returns:
            list: List of empty datasets
            dict: Dictionary containing the URIs
        """
        empty_dv = []
        write_dict = {}
        for key, _item in self.dataverse_contents.items():
            result = jmespath.search(
                "data[?type=='dataset'].{datasetId: id, protocol: protocol, authority: authority, identifier: identifier, path: path, pathIds: pathIds}",  # noqa: E501
                self.dataverse_contents[key],  # noqa: PLR1733
            )
            if result:
                for item in result:
                    pid = f"{item['protocol']}:{item['authority']}/{item['identifier']}"
                    id = item['datasetId']
                    path = '/' + item['path'] if item['path'] else None
                    path_ids = item['pathIds']
                    dict_to_append = {
                        str(id): {  # pid needs to be converted to string if it's not already
                            'CollectionAlias': self.config['COLLECTION_ALIAS'],
                            'CollectionID': self.config['COLLECTION_ID'],
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

    def replace_key_with_dataset_id(self, dictionary: dict) -> None:
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
        self.meta_dict = new_dict

    def add_path_info(self, ds_dict: dict) -> tuple:
        """Add path_info to the metadata dictionary, handling nested structures."""
        ds_dict_copy = ds_dict.copy()
        for pid_key, pid_value in list(ds_dict_copy.items()):
            pid_key_str = str(pid_key)
            # Traverse the meta_dict to find matching datasetId
            for _meta_key, meta_value in self.meta_dict.items():
                if isinstance(meta_value, dict) and meta_value.get('data', {}).get('datasetId') == int(pid_key_str):
                    # Add path_info to the appropriate nested dictionary
                    meta_value['path_info'] = pid_value
                    # Remove from ds_dict_copy
                    ds_dict_copy.pop(pid_key)
                    break
        return self.meta_dict, ds_dict_copy


    def add_permission_info(self, meta_dict: dict, permission_dict: Optional[dict] = None) -> dict:
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

    def rm_dd_from_failed_uris(self, failed_uris: dict, pid_dict_dd: dict) -> dict:
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
