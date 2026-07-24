"""Functions for validating command line arguments and environment variables."""

from http import HTTPStatus

from loguru import logger
from pydantic import ValidationError
from typer import BadParameter

from dvmeta.models.config import Config
from dvmeta.models.ds_version_tags import DatasetVersionTags
from dvmeta.services.client.http import HttpxClient


def validate_version_type(value: str | float | None) -> str | int | float | None:
    """Validate the value of --version argument.

    Args:
        value: Value of --version argument.

    Returns:
        The validated version value.

    Raises:
        BadParameter: If the value is invalid.
    """
    value = value.lower().strip() if isinstance(value, str) else value

    try:
        model = DatasetVersionTags.model_validate({"version": value})
    except ValidationError:
        msg = f'Invalid version: {value}. Must be "draft", "latest", "latest-published", or a number like "1" or "1.2".'
        raise BadParameter(msg) from None
    return model.version


def validate_connection(config: Config) -> bool:
    """Validate connection to the Dataverse repository.

    Args:
        config: The configuration object containing the base URL and API token.

    Returns:
        True if the API token is valid, False otherwise.

    Raises:
        BadParameter: If the connection to the Dataverse repository fails.
    """
    logger.info("Checking the connection to the Dataverse repository...")
    client = HttpxClient(config)

    if config.api_token:
        response = client.check_dv_collection(auth=True)
        if response.is_success:
            logger.info(
                f"Connection to the dataverse repository {config.base_url} with API Token is successful."
            )
            return True
        if response.status_code != HTTPStatus.UNAUTHORIZED:
            msg = f"Failed to connect to the Dataverse repository at {config.base_url} (status {response.status_code}). Please check the URL or your API token and try again."
            raise BadParameter(msg)
        logger.warning(
            "The API Token was rejected (401 Unauthorized). Will try to crawl without the API Token."
        )

    if not client.check_dv_collection(auth=False).is_success:
        msg = f"Failed to connect to the Dataverse repository at {config.base_url}. Please check the URL or your API token and try again."
        raise BadParameter(msg)

    logger.info(f"Connection to the dataverse repository {config.base_url} is successful.")
    return False
