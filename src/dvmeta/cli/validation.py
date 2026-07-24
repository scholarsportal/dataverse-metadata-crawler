"""Functions for validating command line arguments and environment variables."""

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
        result = client.authenticate_api_token()
        if result is True:
            msg = f"Connection to the dataverse repository {config.base_url} with API Token is successful."
            logger.info(msg)
            return True
        if result is False:
            msg = "Failed to authenticate the API Token with the repository. Will try to crawl without the API Token."
            logger.warning(msg)

    # Always check basic connection whether API auth failed or wasn't provided
    client = HttpxClient(config)
    result = client.authenticate_dv_connection()
    if result is False:
        msg = f"Failed to connect to the dataverse repository: {config.base_url}. Exiting..."
        logger.error(msg)
        raise BadParameter(msg)

    logger.info(f"Connection to the dataverse repository {config.base_url} is successful.")
    return False
