"""The dataverse API endpoints used in the crawler."""

from __future__ import annotations

from typing import TYPE_CHECKING, get_args

from dvmeta.models.ds_version_tags import DatasetVersionKeyword

if TYPE_CHECKING:
    from dvmeta.models.ds_version_tags import DatasetVersionTag


class Endpoints:
    """Endpoints for the Dataverse API."""

    @staticmethod
    def search() -> str:
        """Search endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/search.html

        Returns
        -------
        str
        """
        return "api/search"

    @staticmethod
    def ds_json(
        dataset_id: str, version: DatasetVersionTag = "latest", *, return_owners: bool = True
    ) -> str:
        """Dataset JSON representation endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#get-json-representation-of-a-dataset

        Parameters
        ----------
        dataset_id : str
        version : DatasetVersionTag, optional
            By default, "latest". Allowed values are "draft", "latest", "latest-published", or a number like "1" or "1.2".
        return_owners : bool, optional
            By default, True. Whether to return the owners of the dataset (hierarchical information).

        Returns
        -------
        str
        """  # ruff:ignore[doc-line-too-long]
        url = f"api/datasets/{dataset_id}"

        # Handle inputs if version is not in the allowed values
        if version not in set(get_args(DatasetVersionKeyword)):
            version = "latest"

        if version != "latest" and version in DatasetVersionKeyword:
            url += f"/versions/:{version}"
        elif isinstance(version, int | float):
            url += f"/versions/{version}"

        if return_owners:
            url += "?returnOwners=true"

        return url

    @staticmethod
    def ds_permissions(dataset_id: str | int) -> str:
        """Dataset permissions endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#list-role-assignments-in-a-dataset

        Parameters
        ----------
        dataset_id : str | int

        Returns
        -------
        str
        """
        return f"api/datasets/{dataset_id}/assignments"

    @staticmethod
    def dv_json(dataverse_id: str) -> str:
        """Dataverse JSON representation endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#view-a-dataverse-collection

        Parameters
        ----------
        dataverse_id : str

        Returns
        -------
        str
        """
        return f"api/dataverses/{dataverse_id}"

    @staticmethod
    def user_info() -> str:
        """User info endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#get-user-information-in-json-format

        Returns
        -------
        str
        """
        return "api/users/:me"

    @staticmethod
    def version_info() -> str:
        """Version info endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#show-dataverse-software-version-and-build-number

        Returns
        -------
        str
        """
        return "api/info/version"
