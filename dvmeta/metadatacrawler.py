"""Crawl metadata of datasets in a collection."""
import httpx
from httpxclient import HttpxClient


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
        self.config = config
        self.url_tree = f"{config['BASE_URL']}/api/info/metrics/tree?parentAlias={config['COLLECTION_ALIAS']}"
        self.http_success_status = 200
        self.url_dataverse = f"{config['BASE_URL']}/api/dataverses"
        self.count = 0
        self.last_printed_count = 0
        self.write_dict = {}
        self.failed_dict = []
        self.url = None
        self.client = HttpxClient(config)

    def _get_dataset_content_url(self, identifier: str) -> str:
        return f"{self.config['BASE_URL']}/api/datasets/:persistentId/versions/:{self.config['VERSION']}?persistentId={identifier}"  # noqa: E501

    def _get_permission_url(self, identifier: str) -> str:
        return f"{self.config['BASE_URL']}/api/datasets/{identifier}/assignments"

    def _get_dataverse_contents_url(self, identifier: str) -> str:
        return f"{self.config['BASE_URL']}/api/dataverses/{identifier}/contents"

    def _get_tree_url(self, parent_alias: str | None = None) -> str:
        if parent_alias:
            return f"{self.config['BASE_URL']}/api/info/metrics/tree?parentAlias={self.config['COLLECTION_ALIAS']}"
        return f"{self.config['BASE_URL']}/api/info/metrics/tree"

    def get_collections_tree(self, parent_alias: str | None = None) -> httpx.Response | None:
        """Get the tree structure of the collection.

        Returns:
            dict: Dictionary containing the tree structure of the collection
        """
        response = self.client.sync_get(self._get_tree_url(parent_alias))

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
        url_list = [self._get_dataverse_contents_url(identifier) for identifier in id_list]

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
        """Crawl complete metadata of datasets."""
        url_list = [self._get_dataset_content_url(identifier) for identifier in id_list]

        response = await self.client.async_get(url_list)

        dataset_meta = {}
        failed_dataset_meta = {}

        for item in response:
            if item and item.status_code == self.http_success_status and item.json():
                dataset_persistent_idd = item.json().get('data').get('datasetPersistentId')
                dataset_meta[dataset_persistent_idd] = item.json()
            else:
                failed_dataset_meta[str(item.url)] = item.status_code

        return dataset_meta, failed_dataset_meta

    async def get_datasets_permissions(self, id_list: list) -> tuple[dict, dict]:
        """Crawl permissions of datasets."""
        id_url_dict = {self._get_permission_url(identifier): identifier for identifier in id_list}

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
