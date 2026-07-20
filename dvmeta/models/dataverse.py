"""Models for the API responses."""

from typing import Literal

from pydantic import BaseModel, Field

# ruff: noqa: N815


class DvResponse(BaseModel):
    """Model for the collections tree response."""

    status: str
    data: dict


class DatasetVersionTags(BaseModel):
    """Permitted dataset version type."""

    version: Literal["draft", "latest", "latest-published"] | float | int


class DatasetField(BaseModel):
    """Base Dataverse metadata field."""

    typeName: str
    typeClass: Literal[
        "primitive",
        "compound",
        "controlledVocabulary",
    ]
    multiple: bool = False
    value: object


class MetadataBlock(BaseModel):
    """Dataverse metadata block."""

    displayName: str | None = None
    name: str
    fields: list[DatasetField]

    @property
    def field_map(self) -> dict[str, DatasetField]:
        """Return fields indexed by typeName."""
        return {field.typeName: field for field in self.fields}

    def get_field(
        self,
        field_name: str,
    ) -> DatasetField | None:
        """Return a DatasetField by typeName."""
        return self.field_map.get(field_name)

    def get_value(
        self,
        field_name: str,
        default: object = None,
    ) -> object:
        """Return field value."""
        field = self.get_field(field_name)

        if field is None:
            return default

        return field.value


class MetadataBlocks(BaseModel):
    """Dataverse metadata blocks."""

    citation: MetadataBlock | None = None


class DatasetVersion(BaseModel):
    """Dataverse latest version."""

    datasetPersistentId: str | None = None
    versionState: str | None = None
    lastUpdateTime: str | None = None
    releaseTime: str | None = None
    createTime: str | None = None
    termsOfUse: str | None = None
    termsOfAccess: str | None = None
    contactForAccess: str | None = None
    datasetType: str | None = None
    license: dict[str, object] | None = None
    fileAccessRequest: bool | None = None

    metadataBlocks: MetadataBlocks = Field(default_factory=MetadataBlocks)


class DatasetData(BaseModel):
    """Dataverse dataset."""

    id: int | None = None
    datasetId: int | None = None

    datasetVersion: DatasetVersion | None = None


class CitationAccessor:
    """Helper for citation metadata."""

    def __init__(
        self,
        citation_block: MetadataBlock,
    ) -> None:
        self.block = citation_block

    def get(
        self,
        field_name: str,
        default: object = None,
    ) -> object:
        """Return raw field value."""
        return self.block.get_value(
            field_name,
            default,
        )

    def get_compound_values(
        self,
        field_name: str,
        child_field: str,
    ) -> list[object]:
        """Return values from compound fields."""
        rows = self.get(field_name, [])

        result = []

        for row in rows:
            child = row.get(child_field)

            if child:
                result.append(
                    child.get("value"),
                )

        return result
