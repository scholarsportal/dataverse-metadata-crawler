"""The search parameters for the Dataverse Search API.

Docs: https://borealisdata.ca/guides/en/latest/api/search.html

# Note: the publicationStatus fq seems to be available since 6.4 (https://github.com/IQSS/dataverse/issues/10733).
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SearchSort(StrEnum):
    NAME = "name"
    DATE = "date"
    SCORE = "score"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ItemType(StrEnum):
    DATASET = "dataset"
    DATAVERSE = "dataverse"
    FILE = "file"


class DataverseSearchParams(BaseModel):
    """Dataverse search API query parameters."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    q: str = "*"
    type: list[ItemType] | None = Field(default=None, alias="type")
    subtree: list[str] | str | None = None
    sort: SearchSort | None = None
    order: SortOrder | None = None
    per_page: int = 1000
    start: int = 0
    show_relevance: bool = False
    show_facets: bool = False
    fq: list | None = None
    show_entity_ids: bool = False
    show_api_urls: bool = False
    query_entities: bool = True
    metadata_fields: list[str] | None = None
    geo_point: str | None = None
    geo_radius: str | None = None
    show_type_counts: bool = False
    show_collections: bool = False
    search_service: str | None = None

    @model_validator(mode="after")
    def _validate_geo_fields(self) -> "DataverseSearchParams":
        """Validate geo-related fields."""
        if self.geo_point is not None and self.geo_radius is None:
            msg = "geo_radius is required when geo_point is set"
            raise ValueError(msg)

        return self

    @model_validator(mode="after")
    def _validate_limits(self) -> "DataverseSearchParams":
        """Validate numeric limits."""
        if not 1 <= self.per_page <= 1000:
            msg = "per_page must be between 1 and 1000"
            raise ValueError(msg)

        if self.start < 0:
            msg = "start must be greater than or equal to 0"
            raise ValueError(msg)

        return self

    def to_params(self) -> list[tuple[str, str | int | float | None]]:  # noqa: C901, PLR0912
        """Convert the model into HTTP query parameters.

        Returns
        -------
        list[tuple[str, str | int | float | None]]
        """
        params: list[tuple[str, str | int | float | None]] = [("q", self.q)]

        if self.type:
            params.extend(("type", str(value)) for value in self.type)

        if self.subtree:
            if isinstance(self.subtree, str):
                params.append(("subtree", self.subtree))
            else:
                params.extend(("subtree", value) for value in self.subtree)

        if self.sort is not None:
            params.append(("sort", self.sort.value))

        if self.order is not None:
            params.append(("order", self.order.value))

        params.append(("per_page", str(self.per_page)))
        params.append(("start", str(self.start)))

        if self.show_relevance:
            params.append(("show_relevance", "true"))

        if self.show_facets:
            params.append(("show_facets", "true"))

        if self.fq:
            params.extend(("fq", value) for value in self.fq if value is not None)

        if self.show_entity_ids:
            params.append(("show_entity_ids", "true"))

        if self.show_api_urls:
            params.append(("show_api_urls", "true"))

        if not self.query_entities:
            params.append(("query_entities", "false"))

        if self.metadata_fields:
            params.extend(("metadata_fields", value) for value in self.metadata_fields)

        if self.geo_point is not None:
            params.append(("geo_point", self.geo_point))

        if self.geo_radius is not None:
            params.append(("geo_radius", self.geo_radius))

        if self.show_type_counts:
            params.append(("show_type_counts", "true"))

        if self.show_collections:
            params.append(("show_collections", "true"))

        if self.search_service is not None:
            params.append(("search_service", self.search_service))

        return params
