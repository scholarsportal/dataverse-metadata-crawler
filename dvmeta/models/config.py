"""Module for the configuration settings of the metadata crawler."""

from pydantic import AliasChoices
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from dvmeta.models.log_level import LogLevel


class Config(BaseSettings):
    """Model for the configuration settings."""

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
    )

    api_token: str | None = Field(
        None,
        validation_alias=AliasChoices(
            'API_TOKEN',
            'API_KEY',  # Keep for backward compatibility.
        ),
    )
    base_url: str = Field(
        'https://borealisdata.ca/',
    )
    version: str = Field(
        default='latest',
    )
    collection_alias: str = ''
    collection_id: int | str | None = None
    collection_name: str | None = None
    metadata_source: str | None = None
    semaphore_limit: int = 5
    log_level: LogLevel = Field(
        LogLevel.INFO,
        validation_alias=AliasChoices(
            'log_level',
            'LOG_LEVEL',
        ),
    )
