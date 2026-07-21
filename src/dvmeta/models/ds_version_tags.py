"""Tags for dataset versions in Dataverse."""

from typing import Literal, TypeAlias

from pydantic import BaseModel

DatasetVersionKeyword: TypeAlias = Literal["draft", "latest", "latest-published"]

DatasetVersionTag = DatasetVersionKeyword | float | int | None


class DatasetVersionTags(BaseModel):
    """Permitted dataset version type."""

    version: DatasetVersionTag
