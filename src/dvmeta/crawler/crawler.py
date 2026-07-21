"""The new crawler module for dvmeta.

Flow:
1. Use the search API -> Get all the datasets in the Dataverse collection (including all the children)
2. For each dataset, get the metadata using the dataset Native API endpoint
3. Have the option to get the path using the OAIMPH endpoint
4. Have the option to get the permission metadata for each dataset
5. Export the metadata to JSON and CSV files


"""

import httpx2

from dvmeta.models.config import Config
from dvmeta.models.ds_version_tags import DatasetVersionTag
from dvmeta.models.search_params import DataverseSearchParams
from dvmeta.services.client.endpoints import Endpoints
from dvmeta.services.client.http import HttpxClient


class MetaDataCrawler:
    """Crawl metadata of datasets in a collection."""

    def __init__(self, config: Config) -> None:
        """Initialize the class with the configuration settings."""
        self.config = config
        self.client = HttpxClient(self.config)

    def get_dataverse_collection_records(self) -> dict:
        """Get the collection metadata of the Dataverse collection."""
        url = Endpoints.dv_json(self.config.collection_alias)
        response = self.client.sync_get(url)

        if response is None:
            return {}

        return response.json()

    def get_search_result(self, base_search_params: DataverseSearchParams) -> dict:
        """Get the dataset records in the Dataverse collection (recursively, including all the children).

        Uses the Search API.

        Parameters
        ----------
        base_search_params : DataverseSearchParams
            The base search parameters for the API call.

        Returns
        -------
        dict: The search result from the Dataverse Search API.
        """
        search_url = Endpoints.search()

        base_search_params.per_page = 1
        base_search_params.start = 0

        response = self.client.sync_get(search_url, params=base_search_params.to_params())

        return response.json() if response and response.json() is not None else {}

    async def get_dataverse_ds_records_async(
        self, start_parameters: tuple[int, ...], search_params: DataverseSearchParams
    ) -> list:
        """Asynchronously get the dataset records in the Dataverse collection (recursively, including all the children).

        Uses the Search API.

        Parameters
        ----------
            start_parameters (tuple[int]): A tuple of starting indices for the search results.
            search_params (DataverseSearchParams): The search parameters for the API call.

        Returns
        -------
            list: A list of dataset metadata dictionaries
        """  # ruff:ignore[doc-line-too-long]
        search_url = Endpoints.search()

        search_params.per_page = 1000

        url_list = [
            httpx2.Request(
                "GET",
                search_url,
                params=search_params.model_copy(update={"start": start}).to_params(),
            )
            for start in start_parameters
        ]

        responses = await self.client.async_get(url_list)
        return [
            item
            for response in responses
            for item in response.json().get("data", {}).get("items", [])
        ]

    async def get_dataset_metadata(
        self, dataset_ids: list[str], version: DatasetVersionTag | None
    ) -> dict:
        """Get the metadata of a dataset using the dataset Native API endpoint.

        Parameters
        ----------
            dataset_ids (list): A list of dataset database IDs (global_id in search API)
            version (str | None): The version of the dataset

        Returns
        -------
            dict: A dictionary mapping dataset IDs to their metadata
        """
        url_list: list = [
            Endpoints.ds_json(dataset_id=dataset_id, version=version) for dataset_id in dataset_ids
        ]

        response = await self.client.async_get(url_list)

        return {
            dataset_id: res.json()
            for dataset_id, res in zip(dataset_ids, response, strict=False)
            if res is not None
        }

    async def get_dataset_permissions(self, dataset_ids: list) -> dict:
        """Get the permission metadata of a dataset using the dataset permissions API endpoint.

        Parameters
        ----------
            dataset_ids (list): A list of dataset (entity) IDs

        Returns
        -------
            dict: A dictionary mapping dataset IDs to their permission metadata
        """
        url_list = [Endpoints.ds_permissions(dataset_id) for dataset_id in dataset_ids]

        response = await self.client.async_get(url_list)

        return {
            dataset_id: res.json()
            for dataset_id, res in zip(dataset_ids, response, strict=False)
            if res is not None
        }
