"""Crawl metadata of datasets in a collection."""
from urllib.parse import urlencode
from urllib.parse import urljoin

import httpx
from custom_logging import CustomLogger
from httpxclient import HttpxClient


# Set up logging
logger = CustomLogger.get_logger(__name__)


class MetaDataCrawler:
    """Crawl metadata of datasets in a collection.

    Attributes:
        config (dict): Configuration dictionary

    Methods:
        get_collections_tree: Get the tree structure of the collection
        get_dataverse_contents: Get basic metadata of datasets in a collection
        crawl_datasets_meta: Crawl metadata of datasets in a collection
        _get_dataset_content_url: Get the URL of the dataset content
        _get_permission_url: Get the URL of the dataset permission
        _get_dataverse_contents_url: Get the URL of the dataverse contents
        _get_tree_url: Get the URL of the tree structure
    """

    def __init__(self, config: dict) -> None:
        """Initialize the class with the configuration settings."""
        self.config = self._define_headers(config)
        self.http_success_status = 200
        self.count = 0
        self.last_printed_count = 0
        self.write_dict = {}
        self.failed_dict = []
        self.url = None
        self.client = HttpxClient(self.config)

    @staticmethod
    def _define_headers(config: dict) -> dict[str, str]:
        """Define the headers for the HTTP request.

        Args:
            config (dict): Configuration dictionary

        Returns:
            dict[str, str]: Dictionary containing the headers
        """
        headers = {'Accept': 'application/json'}

        api_key = config.get('API_KEY')
        if api_key and str(api_key).lower() != 'none':
            headers['X-Dataverse-key'] = api_key

        config['HEADERS'] = headers

        return config

    def _build_url(self, path: str, query_params: dict | None = None) -> str:
        """Build a URL with proper handling of slashes and query parameters.

        Args:
            path: The API path to append to the base URL
            query_params: Optional dictionary of query parameters

        Returns:
            A properly formatted URL
        """
        base_url = self.config['BASE_URL']
        url = urljoin(base_url, path)

        if query_params:
            return f'{url}?{urlencode(query_params)}'
        return url

    def _parse_dataset_content_url(self, identifier: str) -> str:
        # Note: This URL has a specific format with ':' placeholders
        path = f"/api/datasets/:persistentId/versions/:{self.config['VERSION']}"
        query_params = {'persistentId': identifier}
        return self._build_url(path, query_params)

    def _parse_permission_url(self, identifier: str) -> str:
        path = f'/api/datasets/{identifier}/assignments'
        return self._build_url(path)

    def _parse_dataverse_contents_url(self, identifier: str) -> str:
        path = f'/api/dataverses/{identifier}/contents'
        return self._build_url(path)

    def _parse_tree_url(self, parent_alias: str | None = None) -> str:
        path = '/api/info/metrics/tree'
        if parent_alias:
            query_params = {'parentAlias': self.config['COLLECTION_ALIAS']}
            return self._build_url(path, query_params)
        return self._build_url(path)

    def get_collections_tree(self, parent_alias: str | None = None) -> httpx.Response | None:
        """Get the tree structure of the collection.

        Returns:
            dict: Dictionary containing the tree structure of the collection
        """
        response = self.client.sync_get(self._parse_tree_url(parent_alias))

        if response and response.status_code == self.http_success_status:
            return response
        return None

    async def get_dataverse_contents(self, id_list: list) -> tuple[dict, dict]:
        """Get basic metadata of datasets in all collections.

        Args:
            id_list (list): List of dataset IDs

        Returns:
            tuple[dict, dict]: Tuple containing two dictionaries:
                - dataverse_contents: Successful metadata indexed by identifier
                - failed_dataverse_contents: Failed metadata indexed by identifier
        """  # noqa: W505
        url_list = [self._parse_dataverse_contents_url(identifier) for identifier in id_list]

        response = await self.client.async_get(url_list)

        dataverse_contents = {}
        failed_dataverse_contents = {}

        for identifier, item in zip(id_list, response):
            if item and item.status_code == self.http_success_status and item.json():
                dataverse_contents[identifier] = item.json()
            else:
                failed_dataverse_contents[identifier] = {
                    'url': item.url if item else None,
                    'status_code': item.status_code if item else None,
                }

        return dataverse_contents, failed_dataverse_contents

    async def get_datasets_meta(self, id_list: list) -> tuple[dict, dict]:
        """Crawl complete metadata of datasets.

        Args:
            id_list (list): List of dataset IDs

        Returns:
            tuple[dict, dict]: Tuple containing two dictionaries:
                - dataset_meta: Successful metadata indexed by persistent ID
                - failed_dataset_meta: Failed metadata indexed by URL
        """
        url_list = [self._parse_dataset_content_url(identifier) for identifier in id_list]

        response = await self.client.async_get(url_list)

        dataset_meta = {}
        failed_dataset_meta = {}

        for item in response:
            if item and item.status_code == self.http_success_status and item.json():
                dataset_persistent_idd = item.json().get('data').get('datasetPersistentId')
                dataset_meta[dataset_persistent_idd] = item.json()
            elif item and item.status_code != self.http_success_status:
                failed_dataset_meta[str(item.url)] = item.status_code
            elif isinstance(item, list):
                failed_dataset_meta[item[0]] = item[1]

        return dataset_meta, failed_dataset_meta

    async def get_datasets_permissions(self, id_list: list) -> tuple[dict, dict]:
        """Crawl permissions of datasets.

        Args:
            id_list (list): List of dataset IDs

        Returns:
            tuple[dict, dict]: Tuple containing two dictionaries:
                - permission_meta: Successful metadata indexed by persistent ID
                - failed_permission_meta: Failed metadata indexed by URL
        """
        id_url_dict = {self._parse_permission_url(identifier): identifier for identifier in id_list}

        responses = await self.client.async_get(list(id_url_dict.keys()))

        permission_meta = {}
        failed_permission_meta = {}

        for resp in responses:
            # Look up the identifier by the original request URL
            identifier = id_url_dict.get(str(resp.url))

            if resp.status_code == self.http_success_status and resp.json():
                permission_meta[identifier] = resp.json()
            else:
                failed_permission_meta[str(resp.url)] = resp.status_code

        return permission_meta, failed_permission_meta
