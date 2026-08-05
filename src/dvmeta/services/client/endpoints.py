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

        Returns:
            str: The search endpoint URL.
        """
        return "api/search"

    @staticmethod
    def ds_json(
        dataset_id: str, version: DatasetVersionTag = "latest", *, return_owners: bool = True
    ) -> str:
        """Dataset JSON representation endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#get-json-representation-of-a-dataset

        Args:
            dataset_id (str): The dataset's persistent ID or database ID.
            version (Literal["draft", "latest", "latest-published"] | int | float | None): The dataset version to fetch.
            return_owners (bool): Whether to include the owning collection hierarchy.

        Returns:
            str: The dataset JSON representation endpoint URL.
        """  # ruff:ignore[doc-line-too-long]
        url = f"api/datasets/{dataset_id}"

        # Handle inputs if version is not in the allowed values
        if version not in set(get_args(DatasetVersionKeyword)) and not isinstance(version, int | float):
            version = "latest"

        if version != "latest" and version in get_args(DatasetVersionKeyword):
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

        Args:
            dataset_id: The dataset's persistent ID or database ID.

        Returns:
            str: The dataset permissions endpoint URL.
        """
        return f"api/datasets/{dataset_id}/assignments"

    @staticmethod
    def dv_json(dataverse_id: str) -> str:
        """Dataverse JSON representation endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#view-a-dataverse-collection

        Args:
            dataverse_id: The Dataverse collection's alias or database ID.

        Returns:
            str: The Dataverse JSON representation endpoint URL.
        """
        return f"api/dataverses/{dataverse_id}"

    @staticmethod
    def user_info() -> str:
        """User info endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#get-user-information-in-json-format

        Returns:
            str: The user info endpoint URL.
        """
        return "api/users/:me"

    @staticmethod
    def version_info() -> str:
        """Version info endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#show-dataverse-software-version-and-build-number

        Returns:
            str: The version info endpoint URL.
        """
        return "api/info/version"
