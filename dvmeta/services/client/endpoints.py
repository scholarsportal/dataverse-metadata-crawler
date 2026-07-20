"""The dataverse API endpoints used in the crawler."""

from typing import Literal


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
        dataset_id: str, version: Literal["latest", "latest-published", "draft"] = "latest"
    ) -> str:
        """Dataset JSON representation endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#get-json-representation-of-a-dataset

        Parameters
        ----------
        dataset_id : str
        version : Literal["latest", "latest-published", "draft"], optional
            By default, "latest".

        Returns
        -------
        str
        """
        url = f"api/datasets/{dataset_id}"

        # Handle inputs if version is not in the allowed values
        if version not in {"latest", "latest-published", "draft"}:
            version = "latest"

        if version != "latest":
            url += f"/versions/:{version}"

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
