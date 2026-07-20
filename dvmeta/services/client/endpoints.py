"""The dataverse API endpoints used in the crawler."""


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
    def ds_json(dataset_id: str | int, draft: bool = False) -> str:
        """Dataset JSON representation endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#get-json-representation-of-a-dataset

        Note: This endpoint is currently not used. Just for keeping and future use.

        Parameters
        ----------
        draft : bool, optional
            By default, False.
        dataset_id : str | int

        Returns
        -------
        str
        """
        url = f"api/datasets/{dataset_id}"

        if draft:
            url += "/:draft"
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
    def ds_meta_exporters(
        persistent_id: str, exporter: str = "dataverse_json", version: str | None = None
    ) -> str:
        """Dataset metadata exporters endpoint.

        Docs: https://borealisdata.ca/guides/en/latest/api/native-api.html#export-metadata-of-a-dataset-in-various-formats

        Parameters
        ----------
        version : str | None, optional
            By default, None.
        exporter : str, optional
            By default, "dataverse_json".
        persistent_id : str

        Returns
        -------
        str
        """
        if version is not None and isinstance(version, str):
            return f"api/datasets/export?exporter={exporter}&persistentId={persistent_id}&version=:{version}"
        return f"api/datasets/export?exporter={exporter}&persistentId={persistent_id}"

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
